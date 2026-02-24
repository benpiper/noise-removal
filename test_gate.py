import numpy as np
from scipy.ndimage import gaussian_filter1d

def apply_noise_gate(audio_data, sample_rate, threshold_db=-40.0):
    threshold_linear = 10 ** (threshold_db / 20)
    window_size = int(sample_rate * 0.01) # 10 ms window
    
    padded = np.pad(audio_data, (window_size//2, window_size - window_size//2), mode='edge')
    cumsum_sq = np.cumsum(padded**2)
    # len(cumsum_sq) = len(audio_data) + window_size
    # we want rms of length = len(audio_data)
    rms = np.sqrt((cumsum_sq[window_size:] - cumsum_sq[:-window_size]) / window_size)
    
    gain_mask = np.where(rms > threshold_linear, 1.0, 0.0)
    smooth_gain = gaussian_filter1d(gain_mask, sigma=sample_rate*0.01)
    
    return audio_data * smooth_gain

print(apply_noise_gate(np.array([0.0, 0.1, 0.5, 0.1, 0.0, 0.0, 0.0]), 100))
