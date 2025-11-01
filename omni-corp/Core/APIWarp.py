import requests
import json
import os


def webui_gen(url,body):
    # url = f"http://10.17.188.201:5000/v1/chat/completions/"
    url = f"http://{url}/v1/chat/completions/"
    headers = {
            "Content-Type": "application/json"
                }
    data = {
        "stream":False,
        "messages":[
        {"role":"user",
        "content":body}
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    result = response.text
    result = json.loads(result)
    result = result['choices'][0]['message']['content']
    return result

class Prompt(object):
    def __init__(self,type) -> None:
      self.type = type
      self.system_prompt = '''I am your program analysis assistant, capable of aiding you in code generation, code analysis, and binary code analysis. No matter which programming language you're using, I can provide corresponding assistance. Please tell me your specific requirements.
      '''    
    def gen_prompt(self,question) -> str:
      if type(question) != type(dict()):
          return ""
      Ins = question['Instruction']
      Content = question["Input"]
      prompt = ""
      if self.type == "llama":
          prompt = f"{self.system_prompt}\n##Instruction:\n{Ins}\n##Input:\n{Content}\n##Response:\n"
      elif self.type == "zephyr":
          prompt = f"# <|system|>\n# {self.system_prompt} </s>\n# <|user|>\n {Ins}\n {Content} \n</s>\n# <|assistant|>\n"
      elif self.type == "mistral":
          prompt = f"<s><<SYS>>\n{self.system_prompt}\n<</SYS>>[INST]\n{Ins}\n {Content}\n[/INST]\n"
      elif self.type == "codeqwen":
          # prompt = f"##Instruction:\n{Ins}\n'''\n{Content}\n'''\n##Response:\n"
          prompt = f"<|im_start|>system\nYou are a helpful assistant<|im_end|>\n<|im_start|>user\n{Ins}\n{Content}\n<|im_end|>\n<|im_start|>assistant\n"
      elif self.type == "chatglm":
          prompt = f"<|im_start|> system\nYou are a code assistant, you can answer any question about coding.\n{Ins}\n{Content}\n<|im_end|>\n"
      elif self.type == "content":
          prompt = f"\n{Ins}\n{Content}\n"
      else:
          print(f"[ERROR] 不识别的类型模板 {self.type}")
          os._exit(0)
      return prompt

class llamacpp():
    def __init__(self,host="127.0.0.0.1",port=8080) -> None:
        self.url = f"http://{host}:{str(port)}/completion"
        self.headers = {
        "Content-Type": "application/json"
            }
        
    def run(self,prompt,ctx=16384,temp=1.0,topk=20,topp=0.9,penalty=1.15):
        self.data = {
        "prompt": prompt,
        "n_predict": ctx,
        "temperature":temp,
        "top_k":topk,
        "top_p":topp,
        "repeat_penalty":penalty
    }
        response = requests.post(self.url, json=self.data, headers=self.headers)
        # 打印出响应内容
        result = response.text
        result = json.loads(result)
        return result["content"]


class webui():
    def __init__(self,host="127.0.0.1",port=5000) -> None:
        self.url = f"http://{host}:{str(port)}/api/v1/generate"

    def run(self,prompt,ctx=32768,temp=1.0,topk=20,topp=0.9,penalty=1.15):
        request = {
        'prompt': prompt,
        'max_new_tokens': ctx,
        'auto_max_new_tokens': False,
        'max_tokens_second': 0,

        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',
        'do_sample': True,
        'temperature': temp,
        'top_p': topp,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': penalty,
        'additive_repetition_penalty': 0,
        'repetition_penalty_range': 0,
        'top_k': topk,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'grammar_string': '',
        'guidance_scale': 1,
        'negative_prompt': '',

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 16384,
        'ban_eos_token': False,
        'custom_token_bans': '',
        'skip_special_tokens': True,
        'stopping_strings': []
    }

        response = requests.post(self.url, json=request)

        if response.status_code == 200:
            result = response.json()['results'][0]['text']
            return result
        

def openai(url,prompt):
    # url = "http://10.17.188.201:5000/v1/chat/completions/"
    headers = {
            "Content-Type": "application/json"
                }
    data = {
        "stream":False,
        "messages":[
        {"role":"user",
        "content":prompt}
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    result = response.text
    result = json.loads(result)
    result = result['choices'][0]['message']['content']
    return result
if __name__ == "__main__":
    prompt = Prompt("llama")
# 下面代码存在一个缓冲区溢出漏洞，请指出造成该漏洞的代码，并给出能够触发漏洞的程序输入：
    body = '''
void PngImage::printStructure(std::ostream& out, PrintStructureOption option, size_t depth) {
  if (io_->open() != 0) {
    throw Error(ErrorCode::kerDataSourceOpenFailed, io_->path(), strError());
  }
  if (!isPngType(*io_, true)) {
    throw Error(ErrorCode::kerNotAnImage, "PNG");
  }

  char chType[5];
  chType[0] = 0;
  chType[4] = 0;

  if (option == kpsBasic || option == kpsXMP || option == kpsIccProfile || option == kpsRecursive) {
    const auto xmpKey = upper("XML:com.adobe.xmp");
    const auto exifKey = upper("Raw profile type exif");
    const auto app1Key = upper("Raw profile type APP1");
    const auto iptcKey = upper("Raw profile type iptc");
    const auto softKey = upper("Software");
    const auto commKey = upper("Comment");
    const auto descKey = upper("Description");

    bool bPrint = option == kpsBasic || option == kpsRecursive;
    if (bPrint) {
      out << "STRUCTURE OF PNG FILE: " << io_->path() << std::endl;
      out << " address | chunk |  length | data                           | checksum" << std::endl;
    }

    const size_t imgSize = io_->size();
    DataBuf cheaderBuf(8);

    while (!io_->eof() && ::strcmp(chType, "IEND") != 0) {
      const size_t address = io_->tell();

      size_t bufRead = io_->read(cheaderBuf.data(), cheaderBuf.size());
      if (io_->error())
        throw Error(ErrorCode::kerFailedToReadImageData);
      if (bufRead != cheaderBuf.size())
        throw Error(ErrorCode::kerInputDataReadFailed);

      // Decode chunk data length.
      const uint32_t dataOffset = cheaderBuf.read_uint32(0, Exiv2::bigEndian);
      for (int i = 4; i < 8; i++) {
        chType[i - 4] = cheaderBuf.read_uint8(i);
      }

      // test that we haven't hit EOF, or wanting to read excessive data
      const size_t restore = io_->tell();
      if (dataOffset > imgSize - restore) {
        throw Exiv2::Error(ErrorCode::kerFailedToReadImageData);
      }

      DataBuf buff(dataOffset);
      if (dataOffset > 0) {
        bufRead = io_->read(buff.data(), dataOffset);
        enforce(bufRead == dataOffset, ErrorCode::kerFailedToReadImageData);
      }
      io_->seek(restore, BasicIo::beg);

      // format output
      const int iMax = 30;
      const uint32_t blen = dataOffset > iMax ? iMax : dataOffset;
      std::string dataString;
      // if blen == 0 => slice construction fails
      if (blen > 0) {
        std::stringstream ss;
        ss << Internal::binaryToString(makeSlice(buff, 0, blen));
        dataString = ss.str();
      }
      while (dataString.size() < iMax)
        dataString += ' ';
      dataString.resize(iMax);

      if (bPrint) {
        io_->seek(dataOffset, BasicIo::cur);  // jump to checksum
        byte checksum[4];
        bufRead = io_->read(checksum, 4);
        enforce(bufRead == 4, ErrorCode::kerFailedToReadImageData);
        io_->seek(restore, BasicIo::beg);  // restore file pointer

        out << Internal::stringFormat("%8d | %-5s |%8d | ", static_cast<uint32_t>(address), chType, dataOffset)
            << dataString
            << Internal::stringFormat(" | 0x%02x%02x%02x%02x", checksum[0], checksum[1], checksum[2], checksum[3])
            << std::endl;
      }

      // chunk type
      bool tEXt = std::strcmp(chType, "tEXt") == 0;
      bool zTXt = std::strcmp(chType, "zTXt") == 0;
      bool iCCP = std::strcmp(chType, "iCCP") == 0;
      bool iTXt = std::strcmp(chType, "iTXt") == 0;
      bool eXIf = std::strcmp(chType, "eXIf") == 0;

      // for XMP, ICC etc: read and format data
      const auto dataStringU = upper(dataString);
      bool bXMP = option == kpsXMP && findi(dataStringU, xmpKey) == 0;
      bool bExif = option == kpsRecursive && (findi(dataStringU, exifKey) == 0 || findi(dataStringU, app1Key) == 0);
      bool bIptc = option == kpsRecursive && findi(dataStringU, iptcKey) == 0;
      bool bSoft = option == kpsRecursive && findi(dataStringU, softKey) == 0;
      bool bComm = option == kpsRecursive && findi(dataStringU, commKey) == 0;
      bool bDesc = option == kpsRecursive && findi(dataStringU, descKey) == 0;
      bool bDump = bXMP || bExif || bIptc || bSoft || bComm || bDesc || iCCP || eXIf;

      if (bDump) {
        DataBuf dataBuf;
        enforce(dataOffset < std::numeric_limits<uint32_t>::max(), ErrorCode::kerFailedToReadImageData);
        DataBuf data(dataOffset + 1ul);
        data.write_uint8(dataOffset, 0);
        bufRead = io_->read(data.data(), dataOffset);
        enforce(bufRead == dataOffset, ErrorCode::kerFailedToReadImageData);
        io_->seek(restore, BasicIo::beg);
        size_t name_l = std::strlen(data.c_str()) + 1;  // leading string length
        enforce(name_l < dataOffset, ErrorCode::kerCorruptedMetadata);

        auto start = static_cast<uint32_t>(name_l);
        bool bLF = false;

        // decode the chunk
        bool bGood = false;
        if (tEXt) {
          bGood = tEXtToDataBuf(data.c_data(name_l), dataOffset - name_l, dataBuf);
        }
        if (zTXt || iCCP) {
          enforce(dataOffset - name_l - 1 <= std::numeric_limits<uLongf>::max(), ErrorCode::kerCorruptedMetadata);
          bGood = zlibToDataBuf(data.c_data(name_l + 1), static_cast<uLongf>(dataOffset - name_l - 1),
                                dataBuf);  // +1 = 'compressed' flag
        }
        if (iTXt) {
          bGood = (3 <= dataOffset) && (start < dataOffset - 3);  // good if not a nul chunk
        }
        if (eXIf) {
          bGood = true;  // eXIf requires no pre-processing
        }

        // format is content dependent
        if (bGood) {
          if (bXMP) {
            while (start < dataOffset && !data.read_uint8(start))
              start++;                  // skip leading nul bytes
            out << data.c_data(start);  // output the xmp
          }

          if (bExif || bIptc) {
            DataBuf parsedBuf = PngChunk::readRawProfile(dataBuf, tEXt);
#ifdef EXIV2_DEBUG_MESSAGES
            std::cerr << Exiv2::Internal::binaryToString(
                             makeSlice(parsedBuf.c_data(), parsedBuf.size() > 50 ? 50 : parsedBuf.size(), 0))
                      << std::endl;
#endif
            if (!parsedBuf.empty()) {
              if (bExif) {
                // create memio object with the data, then print the structure
                MemIo p(parsedBuf.c_data(6), parsedBuf.size() - 6);
                printTiffStructure(p, out, option, depth + 1);
              }
              if (bIptc) {
                IptcData::printStructure(out, makeSlice(parsedBuf, 0, parsedBuf.size()), depth);
              }
            }
          }

          if (bSoft && !dataBuf.empty()) {
            DataBuf s(dataBuf.size() + 1);                         // allocate buffer with an extra byte
            std::copy(dataBuf.begin(), dataBuf.end(), s.begin());  // copy in the dataBuf
            s.write_uint8(dataBuf.size(), 0);                      // nul terminate it
            const auto str = s.c_str();                            // give it name
            out << Internal::indent(depth) << buff.c_str() << ": " << str;
            bLF = true;
          }

          if ((iCCP && option == kpsIccProfile) || bComm) {
            out.write(dataBuf.c_str(), dataBuf.size());
            bLF = bComm;
          }

          if (bDesc && iTXt) {
            DataBuf decoded = PngChunk::decodeTXTChunk(buff, PngChunk::iTXt_Chunk);
            out.write(decoded.c_str(), decoded.size());
            bLF = true;
          }

          if (eXIf && option == kpsRecursive) {
            // create memio object with the data, then print the structure
            MemIo p(data.c_data(), dataOffset);
            printTiffStructure(p, out, option, depth + 1);
          }

          if (bLF)
            out << std::endl;
        }
      }
      io_->seek(dataOffset + 4, BasicIo::cur);  // jump past checksum
      if (io_->error())
        throw Error(ErrorCode::kerFailedToReadImageData);
    }
  }
}

static void readChunk(DataBuf& buffer, BasicIo& io) {
#ifdef EXIV2_DEBUG_MESSAGES
  std::cout << "Exiv2::PngImage::readMetadata: Position: " << io.tell() << std::endl;
#endif
  const size_t bufRead = io.read(buffer.data(), buffer.size());
  if (io.error()) {
    throw Error(ErrorCode::kerFailedToReadImageData);
  }
  if (bufRead != buffer.size()) {
    throw Error(ErrorCode::kerInputDataReadFailed);
  }
}
```
'''
# 下面的代码中有哪些是适合做libfuzzer的目标测试代码,用Json的格式输出，其中key值为target，value值为函数名构成的List。
#
    # body = "请通过一个gdb插件的例子来展示如何开发一个好的gdb python插件"
    question = {}
    question["Instruction"] = "上面这个函数主要进行了什么操作"
    question["Input"] = body

    myprompt = prompt.gen_prompt(question)

    api = llamacpp(host="10.17.188.201",port=7070)
    # api = llamacpp(host="127.0.0.1",port=7070)
    result = api.run(myprompt)
    print(result)