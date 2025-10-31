#!/bin/bash

echo "[+] 关键函数识别"

cd ../../fuzzgoat-master/
rm -rf decode && mkdir decode
touch test.c

cd ../omni-corp/
source omni/bin/activate
python Sel.py -i ../fuzzgoat-master/ -o ../fuzzgoat-master/decode/

echo "[+] 识别完成，函数列表在 fuzzgoat-master/decode/ 中"

echo "[+] 选择 json_parse 函数"

python Gen_by_sel.py -i ../fuzzgoat-master/ -o ../fuzzgoat-master/decode/ -s ../fuzzgoat-master/decode/json_parse.sel

echo "[+] 驱动生成"