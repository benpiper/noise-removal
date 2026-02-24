#!/usr/bin/env python3
"""Cleanscriber - Automated audio noise reduction and transcription cli tool"""

import sys
import argparse
import time
from pathlib import Path
from src.core.audio_processor import AudioProcessor
from src.core.whisper_evaluator import WhisperEvaluator
from src.utils.config_manager import load_config


def main():
    parser = argparse.ArgumentParser(
        description="Cleanscriber: Automated audio cleanup and transcription"
    )
    parser.add_argument(
        "input_file",
        help="Path to the noisy input audio file (defaults to looking inside ./input/)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save the cleaned files (default: ./output)",
    )
    parser.add_argument(
        "--model", default="tiny", help="Whisper model size (default: tiny)"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Config overrides CLI defaults if provided, otherwise respect CLI args
    model_size = config.get("model", args.model)
    output_dir_str = config.get("output_dir", args.output_dir)
    input_dir_str = config.get("input_dir", "input")
    input_file_str = args.input_file

    input_path = Path(input_file_str)

    if not input_path.exists() and not input_path.is_absolute():
        fallback_path = Path(input_dir_str) / input_path
        if fallback_path.exists():
            input_path = fallback_path

    input_path = input_path.resolve()

    if not input_path.exists():
        print(f"Error: file {input_file_str} does not exist.")
        sys.exit(1)

    base_name = input_path.stem
    ext = input_path.suffix

    run_timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir_str).resolve() / f"{base_name}_{run_timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"[{time.strftime('%H:%M:%S')}] Starting Cleanscriber pipeline on {input_path.name}"
    )
    start_time = time.time()

    processor = AudioProcessor(config=config)
    if not processor.load_file(str(input_path)):
        print("Failed to load audio.")
        sys.exit(1)

    print(
        f"[{time.strftime('%H:%M:%S')}] Generating Candidate 0 (Normalized + High-Pass > 80Hz)..."
    )
    candidate_0 = processor.generate_candidate_0()

    print(
        f"[{time.strftime('%H:%M:%S')}] Generating Candidates 1-3 (Noise Reduction profiles)..."
    )
    candidates = processor.generate_noise_candidates()

    initial_candidates = [
        ("Candidate 0", candidate_0, f"{base_name}_candidate_0{ext}"),
        ("Candidate 1", candidates[0], f"{base_name}_candidate_1_nr{ext}"),
        ("Candidate 2", candidates[1], f"{base_name}_candidate_2_nr{ext}"),
        ("Candidate 3", candidates[2], f"{base_name}_candidate_3_nr{ext}"),
    ]

    print(f"[{time.strftime('%H:%M:%S')}] Initializing Whisper model '{model_size}'...")
    evaluator = WhisperEvaluator(model_size=model_size)

    base_best_score = -1.0
    base_best_candidate = None
    base_best_index = -1

    candidate0_score = -1.0
    candidate0_result = None

    all_scores = []

    print(f"[{time.strftime('%H:%M:%S')}] Evaluating initial candidates (0-3)...")
    for i, (name, audio_data, filename) in enumerate(initial_candidates):
        print(f"   => Evaluating {name}...")
        cand_path = output_dir / filename
        processor.save_processed_audio(str(cand_path), audio_data)

        # Evaluate
        result = evaluator.evaluate(str(cand_path))
        score = result["confidence"]
        all_scores.append((name, score))
        print(f"      Confidence Score: {score:.4f}")

        if i == 0:
            candidate0_score = score
            candidate0_result = result

        if score > base_best_score:
            base_best_score = score
            base_best_candidate = audio_data
            base_best_index = i

    print(
        f"[{time.strftime('%H:%M:%S')}] Base winner among (0-3): Candidate {base_best_index} with Score {base_best_score:.4f}"
    )

    print(
        f"[{time.strftime('%H:%M:%S')}] Applying {config.get('noise_gate', -40.0)} dB Noise Gate to Candidate {base_best_index}..."
    )
    base_gated = processor.apply_noise_gate(
        base_best_candidate, config.get("noise_gate", -40.0)
    )
    gated_path = output_dir / f"{base_name}_candidate_{base_best_index}_ng{ext}"
    processor.save_processed_audio(str(gated_path), base_gated)

    print(
        f"[{time.strftime('%H:%M:%S')}] Generating Compression Candidates (4-6) from Gated audio..."
    )
    comp_candidates = processor.generate_compression_candidates(base_gated)

    comp_all = [
        ("Candidate 4", comp_candidates[0], f"{base_name}_candidate_4_comp{ext}"),
        ("Candidate 5", comp_candidates[1], f"{base_name}_candidate_5_comp{ext}"),
        ("Candidate 6", comp_candidates[2], f"{base_name}_candidate_6_comp{ext}"),
    ]

    print(f"[{time.strftime('%H:%M:%S')}] Evaluating compression candidates (4-6)...")

    # The final winner is the best between 4, 5, 6 and 0
    final_best_score = candidate0_score
    final_best_candidate = candidate_0
    final_best_result = candidate0_result
    final_best_name = "Candidate 0"

    for i, (name, audio_data, filename) in enumerate(comp_all):
        print(f"   => Evaluating {name}...")
        cand_path = output_dir / filename
        processor.save_processed_audio(str(cand_path), audio_data)

        result = evaluator.evaluate(str(cand_path))
        score = result["confidence"]
        all_scores.append((name, score))
        print(f"      Confidence Score: {score:.4f}")

        if score > final_best_score:
            final_best_score = score
            final_best_candidate = audio_data
            final_best_result = result
            final_best_name = name

    print(
        f"[{time.strftime('%H:%M:%S')}] Final Winner: {final_best_name} with Score {final_best_score:.4f}"
    )

    print(f"[{time.strftime('%H:%M:%S')}] Saving winning files...")
    out_audio_path = output_dir / f"{base_name}_cleaned{ext}"
    out_txt_path = output_dir / f"{base_name}_cleaned.txt"
    out_srt_path = output_dir / f"{base_name}_cleaned.srt"

    processor.save_processed_audio(str(out_audio_path), final_best_candidate)

    with open(out_txt_path, "w", encoding="utf-8") as f:
        f.write(final_best_result["text"])

    with open(out_srt_path, "w", encoding="utf-8") as f:
        f.write(final_best_result["srt"])

    # Generate summary.md
    summary_path = output_dir / "summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Cleanscriber Run Summary\n\n")
        f.write(f"**Input File:** `{input_path.name}`\n")
        f.write(
            f"**Final Winner:** `{final_best_name}` (Score: {final_best_score:.4f})\n\n"
        )
        f.write("## Candidate Scores\n\n")
        for name, score in all_scores:
            f.write(f"- **{name}:** {score:.4f}\n")
        f.write("\n## Pipeline Configuration\n")
        f.write("- **Model:** " + model_size + " (language='en')\n")
        f.write(
            f"- **Noise Gate:** {config.get('noise_gate', -40.0)} dB applied to Candidate {base_best_index}\n"
        )

        nr_conf = config.get("noise_reduction", {})
        f.write(
            f"- **Noise Reduction:** Min {nr_conf.get('minimal', 0.5)}, Mid {nr_conf.get('middle', 0.75)}, Agg {nr_conf.get('aggressive', 0.9)}\n"
        )

        c_conf = config.get("compressor", {})
        min_c = c_conf.get("minimal", {})
        f.write(
            f"- **Compression** (Min): {min_c.get('ratio', 2.0)}:1 @ {min_c.get('threshold_db', -20.0)}dB\n"
        )
        f.write("- **Compression Candidates Normalization:** 0 dB\n")

    elapsed = time.time() - start_time
    print(f"[{time.strftime('%H:%M:%S')}] Done in {elapsed:.1f} seconds.")
    print(f"Output saved to {output_dir}")


if __name__ == "__main__":
    main()
