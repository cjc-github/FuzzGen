import sys
import os

target_floder = "/root/raw_data/tmp_fuzzer_data"
output_dir = "/root/test/output"
for fld in os.listdir(target_floder):
    full_path = os.path.join(target_floder,fld)
    cmd_str = f"python Gen.py -i {full_path} -o {output_dir}"
    os.system(cmd_str)