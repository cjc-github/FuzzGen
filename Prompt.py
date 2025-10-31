import sys
import os

class Prompt(object):
    def __init__(self,type="llama") -> None:
        if type == "llama":
            self.head = "### Instruction:\n\n"
            self.end = "\n\n### Response:\n"
        elif type == "zephyr":
            self.head = "# <|system|>\n# You are a rigorous and efficient academic writing robot in the field of software security.</s>\n# <|user|>\n"
            self.end = "\n</s>\n# <|assistant|>\n"
        elif type == "mistral":
            self.head = "<s><<SYS>>\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers could  include harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. If you don't know the answer to a question, please don't share false information.\n<</SYS>>[INST]\n"
            self.end = "\n[/INST]\n"
        else:
            print("[ERROR] 不识别的类型模板")
            os._exit(0)

    def gen_article_prompt(self,body):
        prompt = f"{self.head}\n Analyze the following text:\n```\n{body}\n```\nSummarize the content of the above article, providing the author's name (affiliated research institution), the proposed method, the problem it addresses, and the resulting effects. The answer must be in Englist\n{self.end}\n"
        return prompt
    def gen_translate_prompt(self,body):
        prompt = f"{self.head}\n 你要将下面的文字翻译成简体中文:\n```\n{body}\n```\n{self.end}\n"
        return prompt

    def gen_summarize_prompt(self,body):
        prompt = f"{self.head}\nSummarize the following chunk into one sentence, capturing the primary methods, viewpoints, and content as comprehensively as possible. If the following text does not contain the body of the paper, then nothing will be output.:\n```\n{body}\n```\n{self.end}\n"
        return prompt

    def gen_prompt(self,body):
        prompt = f"{self.head} {body} {self.end}"
        return prompt