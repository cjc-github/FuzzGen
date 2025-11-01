#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

#include "json.h"

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t length) {
        json_value* value;
        value = json_parse((const json_char*) Data, length);

        if (value == NULL) {
                return 0;
        }

        json_value_free(value);
        return 0;
}
