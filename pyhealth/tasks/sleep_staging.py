import os
import pickle
import mne


def sleep_staging_sleepedf_fn(record, epoch_seconds=30):
    """Processes a single patient for the sleep staging task.

    Sleep staging aims at predicting the sleep stages (Awake, REM, N1, N2, N3) based on
    the multichannel EEG signals. The task is defined as a multi-class classification.

    Args:
        patient: a list of (root, PSG, Hypnogram) tuples, where PSG is the signal files and Hypnogram
        contains the labels
        epoch_seconds: how long will each epoch be (in seconds)

    Returns:
        samples: a list of samples, each sample is a dict with patient_id, record_id,
            and epoch_path (the path to the saved epoch {"X": signal, "Y": label} as key.

    Note that we define the task as a multi-class classification task.

    Examples:
        >>> from pyhealth.datasets import SleepEDFDataset
        >>> sleepedf = SleepEDFDataset(
        ...         root="/srv/local/data/SLEEPEDF/sleep-edf-database-expanded-1.0.0/sleep-cassette",
        ...     )
        >>> from pyhealth.tasks import sleep_staging_sleepedf_fn
        >>> sleepstage_ds = sleepedf.set_task(sleep_staging_sleepedf_fn)
        >>> sleepstage_ds.samples[0]
        {
            'record_id': 'SC4001-0',
            'patient_id': 'SC4001',
            'epoch_path': '/home/chaoqiy2/.cache/pyhealth/datasets/70d6dbb28bd81bab27ae2f271b2cbb0f/SC4001-0.pkl',
            'label': 'W'
        }
    """

    SAMPLE_RATE = 100

    root, psg_file, hypnogram_file, save_path = (
        record[0]["load_from_path"],
        record[0]["signal_file"],
        record[0]["label_file"],
        record[0]["save_to_path"],
    )
    # get patient id
    pid = psg_file[:6]

    # load signal "X" part
    data = mne.io.read_raw_edf(os.path.join(root, psg_file))

    X = data.get_data()
    # load label "Y" part
    ann = mne.read_annotations(os.path.join(root, hypnogram_file))

    labels = []
    for dur, des in zip(ann.duration, ann.description):
        """
        all possible des:
            - 'Sleep stage W'
            - 'Sleep stage 1'
            - 'Sleep stage 2'
            - 'Sleep stage 3'
            - 'Sleep stage R'
            - 'Sleep stage ?'
            - 'Movement time'
        """
        for _ in range(int(dur) // 30):
            labels.append(des)

    samples = []
    sample_length = SAMPLE_RATE * epoch_seconds
    # slice the EEG signals into non-overlapping windows
    # window size = sampling rate * second time = 100 * epoch_seconds
    for slice_index in range(min(X.shape[1] // sample_length, len(labels))):
        # ingore the no label epoch
        if labels[slice_index] not in [
            "Sleep stage W",
            "Sleep stage 1",
            "Sleep stage 2",
            "Sleep stage 3",
            "Sleep stage R",
        ]:
            continue

        epoch_signal = X[
            :, slice_index * sample_length : (slice_index + 1) * sample_length
        ]
        epoch_label = labels[slice_index][-1]  # "W", "1", "2", "3", "R"
        save_file_path = os.path.join(save_path, f"{pid}-{slice_index}.pkl")

        pickle.dump(
            {
                "signal": epoch_signal,
                "label": epoch_label,
            },
            open(save_file_path, "wb"),
        )

        samples.append(
            {
                "record_id": f"{pid}-0",
                "patient_id": pid,
                "epoch_path": save_file_path,
                "label": epoch_label,  # use for counting the label tokens
            }
        )
    return samples


if __name__ == "__main__":
    from pyhealth.datasets import SleepEDFDataset

    dataset = SleepEDFDataset(
        root="/srv/local/data/SLEEPEDF/sleep-edf-database-expanded-1.0.0/sleep-telemetry",
        dev=True,
        refresh_cache=True,
    )

    sleep_staging_ds = dataset.set_task(sleep_staging_sleepedf_fn)
    print(sleep_staging_ds.samples[0])
    # print(sleep_staging_ds.patient_to_index)
    # print(sleep_staging_ds.record_to_index)
    print(sleep_staging_ds.input_info)
