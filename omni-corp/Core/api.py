# from Core.llamacpp import api as api
import Core.deepseek as api
model_type = ""

with open("gen_config.json") as f:
    import json
    config_dict = json.load(f)
    model_type = config_dict['prompt_type']
    

def run_llm_custom(prompt_str):
    '''
    此函数是所有其他文件调用大语言模型运行的底层接口，以后不需要再其他文件直接调用api
    '''

    if model_type == 'content':
        import Core.deepseek as api
    else:
        from Core.llamacpp import api as api

    result = api.run(prompt_str)
    return result
