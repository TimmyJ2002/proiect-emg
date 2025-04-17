% Step 0: Import data from EMG4.txt
% Adjust the path if necessary
data = readtable('EXPORTED.txt', 'Delimiter', '\t', 'ReadVariableNames', false);

% Step 1: Extract the time and voltage values from the table
time = data.Var1;  % Assuming time is in the first column
voltage = data.Var2;  % Assuming voltage is in the second column

% Step 2: Calculate the offset (mean value of the voltage)
offset = mean(voltage);

% Step 3: Subtract the offset from the voltage values
adjusted_voltage = voltage - offset;

% Step 4: Design a notch filter to remove a specific frequency (e.g., 50 Hz)
% Define the notch filter parameters
Fs = 1000; % Sampling frequency (in Hz), adjust this to match your data
wo = 50 / (Fs / 2); % Notch frequency (e.g., 50 Hz) normalized by the Nyquist frequency
bw = wo / 35; % Bandwidth, can be adjusted for the desired sharpness

% Create the notch filter
notch_filter = designfilt('bandstopiir', 'FilterOrder', 2, ...
                          'HalfPowerFrequency1', wo - bw, 'HalfPowerFrequency2', wo + bw, ...
                          'DesignMethod', 'butter');

% Step 5: Apply the notch filter to the adjusted voltage
filtered_voltage_notch = filtfilt(notch_filter, adjusted_voltage);

% Step 6: Design a bandpass filter for the muscle contraction bandwidth (30-200 Hz)
bandpass_filter = designfilt('bandpassiir', 'FilterOrder', 4, ...
                             'HalfPowerFrequency1', 30 / (Fs / 2), 'HalfPowerFrequency2', 200 / (Fs / 2), ...
                             'DesignMethod', 'butter');

% Step 7: Apply the bandpass filter to the notch filtered voltage
filtered_voltage_band = filtfilt(bandpass_filter, filtered_voltage_notch);

% Step 8_rms: Define the RMS window size (in samples)
window_size = 25; % Adjust this value based on how smooth you want the signal to be

% Step 9_rms: Compute the RMS for each window
rms_voltage = sqrt(movmean(filtered_voltage_band.^2, window_size));

% Step 10: Calculate the mean of the RMS filtered voltage
mean_rms_voltage = mean(rms_voltage);

% Last Step: Plot the final filtered voltage data with the mean line
figure;
plot(time, rms_voltage);
xlabel('Time (s)');
ylabel('Filtered Voltage (mV)');
title('RMS Filtered EMG Data (window size = 25)');
grid on;

% Add a pink line for the mean value
hold on;
yline(mean_rms_voltage, '-.m', 'Mean Voltage');

% Step 11: Find and annotate peaks that cross the mean RMS voltage
crosses_mean = rms_voltage > mean_rms_voltage;
starts = find(diff([0; crosses_mean]) == 1);
ends = find(diff([crosses_mean; 0]) == -1);

for i = 1:length(starts)
    segment = rms_voltage(starts(i):ends(i));
    [peak_value, peak_idx] = max(segment);
    peak_time = time(starts(i) + peak_idx - 1);

    % Plot the peak
    plot(peak_time, peak_value, 'rv', 'MarkerFaceColor', 'r');

    % Annotate the peak with the difference from the mean voltage
    peak_difference = peak_value - mean_rms_voltage;
    text(peak_time, peak_value, sprintf('%.2f mV', peak_difference), 'Color', 'r', ...
        'VerticalAlignment', 'bottom', 'HorizontalAlignment', 'right');

    % Add vertical line from mean to peak
    line([peak_time peak_time], [mean_rms_voltage peak_value], 'Color', 'r', 'LineStyle', '-');
end
% % Your plotting code here
drawnow;  % Forces MATLAB to update the figure window
pause;    % Keeps the figure window open until a key is pressed

% Specify the callback for figure close
set(gcf, 'CloseRequestFcn', @myCloseFcn);

% Function to handle figure closure
function myCloseFcn(~, ~)
    % Write a temporary file to signal that the figure has been closed
    fid = fopen('close_flag.txt', 'w');
    fclose(fid);
    
    % Close the figure
    delete(gcf);
end

% Wait for the figure to close before proceeding
waitfor(gcf);

hold off;