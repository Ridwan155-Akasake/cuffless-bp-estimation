import pandas as pd
import numpy as np
from scipy.signal import resample, find_peaks
from scipy.stats import skew, kurtosis
from scipy.fft import fft
import requests
from sklearn.preprocessing import LabelEncoder

def preprocess_to_features_df(file_path):
    # Load and convert to DataFrame
    response = requests.get(file_path.strip())
    response.raise_for_status()
    data = response.json()
    df = pd.json_normalize(data)

    # Encode gender
    le = LabelEncoder()
    df['userGender'] = le.fit_transform(df['userGender'])

    # Convert array columns to separate columns
    def convert_arrays_to_columns(df, array_columns):
        for col in array_columns:
            array_expanded = pd.DataFrame(df[col].tolist(), index=df.index)
            array_expanded.columns = [f"{col}_{i}" for i in range(array_expanded.shape[1])]
            df = pd.concat([df, array_expanded], axis=1)
            df = df.drop(columns=[col])
        return df

    df = convert_arrays_to_columns(df, ['ir', 'red'])

    ir_cols = [c for c in df.columns if c.startswith("ir_")]
    red_cols = [c for c in df.columns if c.startswith("red_")]

    def resample_to_fixed_length(row, cols, target_len=200):
        arr = row[cols].to_numpy(dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            return np.full(target_len, np.nan)
        return resample(arr, target_len)

    target_length = 200
    ir_resampled = np.vstack(df.apply(lambda row: resample_to_fixed_length(row, ir_cols, target_length), axis=1))
    red_resampled = np.vstack(df.apply(lambda row: resample_to_fixed_length(row, red_cols, target_length), axis=1))

    ir_df = pd.DataFrame(ir_resampled, columns=[f"ir_{i}" for i in range(target_length)])
    red_df = pd.DataFrame(red_resampled, columns=[f"red_{i}" for i in range(target_length)])

    keep_cols = ['spo2', 'heartRate', 'userAge', 'userGender', 'userHeight', 'userWeight', 'userBmi']
    df_clean = pd.concat([df[keep_cols].reset_index(drop=True), ir_df, red_df], axis=1)

    ir_cols = [c for c in df_clean.columns if c.startswith("ir_")]

    def extract_features(signal):
        signal = np.asarray(signal, dtype=float)
        if np.all(np.isnan(signal)):
            return [np.nan] * 12
        mean_signal = np.nanmean(signal)
        median_signal = np.nanmedian(signal)
        std_signal = np.nanstd(signal)
        min_signal = np.nanmin(signal) if not np.all(np.isnan(signal)) else np.nan
        max_signal = np.nanmax(signal) if not np.all(np.isnan(signal)) else np.nan
        range_signal = max_signal - min_signal if not np.all(np.isnan(signal)) else np.nan
        skewness_signal = skew(signal, nan_policy='omit') if len(signal[~np.isnan(signal)]) > 1 else np.nan
        kurtosis_signal = kurtosis(signal, nan_policy='omit') if len(signal[~np.isnan(signal)]) > 3 else np.nan
        non_nan_signal = signal[~np.isnan(signal)]
        peaks, _ = find_peaks(non_nan_signal)
        num_peaks = len(peaks)
        mean_peak_amplitude = np.nanmean(non_nan_signal[peaks]) if num_peaks > 0 else np.nan
        if len(non_nan_signal) == 0:
            return [np.nan] * 12
        fft_values = fft(non_nan_signal)
        fft_freq = np.fft.fftfreq(len(non_nan_signal))
        fft_magnitude = np.abs(fft_values)
        if np.all(fft_magnitude[1:] == 0):
            dominant_freq = np.nan
        else:
            dominant_freq = np.abs(fft_freq[np.argmax(fft_magnitude[1:]) + 1])
        total_energy = np.sum(fft_magnitude**2)
        return [
            mean_signal, median_signal, std_signal, min_signal, max_signal, range_signal,
            skewness_signal, kurtosis_signal, num_peaks, mean_peak_amplitude,
            dominant_freq, total_energy
        ]

    def extract_features_from_df(df_clean, ir_columns):
        features = []
        for i, row in df_clean.iterrows():
            ir_signal = row[ir_columns].values
            ir_features = extract_features(ir_signal)
            demographics = [
                row['userAge'], row['userGender'], row['userHeight'], row['userWeight'],
                row['userBmi'], row['heartRate']
            ]
            features.append(ir_features + demographics)
        return np.array(features)

    # Get the features (X) to pass to the model
    X = extract_features_from_df(df_clean, ir_cols)

    # Define column names for the features
    columns = [
        'mean', 'median', 'std', 'min', 'max', 'range', 'skewness', 'kurtosis', 'num_peaks', 'mean_peak_amplitude', 'dominant_freq',
         'total_energy', 'userAge', 'userGender', 'userHeight', 'userWeight', 'heartRate', 'userBmi'
    ]

    # Return X as a DataFrame (so that the column names are clear)
    X_df = pd.DataFrame(X, columns=columns)
    
    # Returning the features as numpy array for model use
    return X_df.to_numpy()