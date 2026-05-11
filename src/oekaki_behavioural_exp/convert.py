# CSV data reproducer.
# Reads each Records/otherself_records/otherself_record_*.csv and writes
# its delayed and enhanced variants alongside it.

import os

import experiment_data

record_path_template = 'Records/otherself_records/otherself_record_{rec_no}.csv'
save_path_template = 'Records/otherself_records/otherself_record_{rec_no}_{mode_str}.csv'

# Mode codes
# 0: delayed
# 1: enhanced

_rec_no = 0
while True:
    record_path = record_path_template.format(rec_no=_rec_no)
    if not os.path.exists(record_path):
        break
    for _mode in [0, 1]:
        save_path = save_path_template.format(rec_no=_rec_no, mode_str='enhanced' if _mode == 1 else 'delayed')

        traject = experiment_data.Trajectory()
        traject.load_csv(record_path, export_enhanced=_mode == 1, export_delayed=_mode == 0)

        with open(save_path, 'w') as f:
            traject.create_csv(f)
        print(f"wrote: {save_path}")
    _rec_no += 1
