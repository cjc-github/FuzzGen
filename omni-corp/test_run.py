# 测试生成和优化代码
from Core.GenData import *
from Core.CustomAlgorithm import *
from Core.CustomStructure import *
from Core.APIWarp import *
from Core.Utils import *
from Core.api import *
from Core.promptINS import *
import subprocess
gen_file_path = "/root/test/test/qoi-master/test.c"
target_floder= "/root/test/test/qoi-master/"
gen_command = "clang -fsanitize=fuzzer,address -g -O2 test.c"
run_command = "./a.out -max_total_time=20"
fuzzer_code = """
#define QOI_IMPLEMENTATION
#define QOI_NO_STDIO
#include "qoi.h";

#include <stdint.h>
#include "qoi.h"

// LibFuzzer 提供的入口函数，接受一个数据缓冲区和其大小作为参数。
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // 检查输入大小是否合理（例如，至少有一个字节）
    if (size == 0)
        return 0;

    qoi_desc desc;
    void *decoded_pixels = qoi_decode((const char*)data, size, &desc, 4);
    
    // 如果解码失败，直接返回，不再尝试编码
    if (!decoded_pixels) {
        return 0; // 继续进行其他输入的测试
    }

    int out_size;
    void *encoded_data = qoi_encode(decoded_pixels, &desc, &out_size);

    // 如果编码成功且生成了数据，则不需要特别处理，继续进行其他输入的测试
    if (encoded_data) {
        free(encoded_data);  // LibFuzzer 不关心内存释放，但是为了保持良好的实践我们仍然释放它。
    }

    return 0;
}
"""
# 先把文件写入到目标
with open(gen_file_path, "w") as f:
    f.write(fuzzer_code)

# 尝试编译目标
cmd = f"cd {target_floder} && {gen_command}"
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
stdout, error_message = process.communicate()
ins = INS_regenerate_compile(fuzzer_code,error_message)
prompt_str = construct_prompt_str(ins,"","codeqwen")
logger.info(prompt_str)
while len(error_message) > 0:
    print("compile error found")
    result = run_llm_custom(prompt_str)
    logger.info(result)
    content_list = result.split("```c")
    fuzzer_code = ""
    for one_code in content_list:
        if "LLVMFuzzerTestOneInput(" in one_code:
            fuzzer_code = one_code.split("```")[0]
            break
    logger.info(fuzzer_code)
    with open(gen_file_path, "w") as f:
        f.write(fuzzer_code)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    stdout, error_message = process.communicate()
    if len(error_message) == 0:
        print("compile success")
        break

run_command = f"cd {target_floder} && {run_command}"
process = subprocess.Popen(run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
stdout, error_message = process.communicate()
print(stdout)
