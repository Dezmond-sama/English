
import re
import random
import requests
from fake_useragent import UserAgent
import json

class Dictionary:
    @staticmethod
    def split_to_words(sentence):
        sentence = sentence.lower()
        #sentence = re.sub(r"[^\w\-\']+", " ", sentence)
        sentence = re.sub(r"[^a-z\-\']+", " ", sentence)
        sentence = re.sub(r"(\'\s)|(\s\')", " ", sentence)
        sentence = re.sub(r"\-{2,}", "", sentence)
        sentence = re.sub(r"\'(s|ll|ve|re|d|m)\b", "", sentence)
        return (word.strip("' ") for word in sentence.split(" ") if len(word) > 0 and word != "-")

    def __init__(self):
        self.words = {}
        self.sentences = []
        self.tags = {}
        self.ua = UserAgent()
        self.words_data = {}
        self.network_flag = False
        self.autosave_words_data = False
        self.autosave_path = ""

    def read_words_data_file(self, file_name):
        with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
            self.words_data = json.load(f)

    def write_words_data_file(self, file_name):
        with open(file_name, "w", encoding="utf-8", errors="ignore") as f:
            json.dump(self.words_data, f, ensure_ascii=False, indent=4)

    def append(self, sentence, tags):
        if 2 < len(sentence.split()) < 15:
            self.sentences.append(sentence)
            for word in Dictionary.split_to_words(sentence):
                self.words.setdefault(word,{"count": 0, "sentences": [], "tags": {}})
                self.words[word]["count"] += 1
                self.words[word]["sentences"].append(len(self.sentences) - 1)
                self.words[word]["data"] = self.__get_word_data(word)
                if self.autosave_words_data and self.network_flag:
                    self.write_words_data_file(self.autosave_path)
                    self.network_flag = False
                for tag in tags:
                    self.words[word]["tags"][tag] = self.words[word]["tags"].get(tag, 0) + 1
                    self.tags[tag] = self.tags.get(tag, 0) + 1

    def read_book(self, file_name, tags):
        abbreviations = {r"Dr\.": "Dr", r"Mr\.": "Mr", r"St\.": "St", r"Mrs\.": "Mrs"}
        with open(file_name, 'r', encoding='utf-8', errors = 'ignore') as f:
            data = f.read().replace("\n"," ").replace("\""," ").replace("--"," - ")
            for a in abbreviations:
                data = re.sub(a, abbreviations[a], data, flags=re.IGNORECASE)
            for sentence in re.split(r"(?<=[.!?…])\s+(?=[A-Z])", re.sub(r"\s+", " ", data)):
                self.append(sentence, tags)
    
    def sentences_by_word(self, word, samples=0):
        word = word.lower()
        if word in self.words:
            idxs = random.sample(self.words[word]["sentences"], samples) if 0 < samples < len(self.words[word]["sentences"]) else self.words[word]["sentences"]
            return [self.sentences[i] for i in idxs]
        return []
    
    def __get_word_data(self, word):
        return self.words_data[word] if word in self.words_data else self.words_data.setdefault(word, self.__get_data_from_web(word))

    def __get_data_from_web(self, word):
        self.network_flag = True
        link = f"https://english-abc.ru/api/findWord/{word.lower()}"
        data = requests.get(link, headers={'User-Agent': self.ua.random})
        if data.status_code != 200:
            return {}
        data = json.loads(data.content)
        if "words" in data:
            return {
                "transcription":    f'[{data["words"][0].get("transcription", "")}]',
                "translation": data["words"][0].get("main_translation", ""),
                "translations":     data["words"][0].get("translations", []),
            }
        return {}
    def __get_data_from_ling(self, word):
        self.network_flag = True
        link = f"https://api.lingvolive.com/Translation/tutor-cards?text={word}&srcLang=1033&dstLang=1049"
        data = requests.get(link, headers={'User-Agent': self.ua.random})
        if data.status_code != 200:
            return {}
        data = json.loads(data.content)
        if data is None:
            return self.__get_data_from_web(word)
        for item in data:
            if item.get("heading", "").lower() == word:
                return {
                    "transcription": f'[{item.get("transcription", "")}]',
                    "translations": [trans.strip() for trans in item.get("translations", "").split(";")],
                }
        return {}
    def get_word_data(self, word):
        word_info = self.words.get(word.lower(), {})
        data = word_info.get("data", {})
        translations = [data.get("translation")]
        for t in data.get("translations", []):
            if t not in translations:
                translations.append(t)                
        tags = {tag: cnt / self.tags.get(tag, 1) for tag, cnt in word_info.get("tags", {}).items()}
        # norm = tags.get(max(tags, key=lambda x: tags[x]), 1)
        norm = sum(tags.values())
        tags = {tag: round(tags.get(tag, 0) * 100 / norm, 2) for tag in sorted(self.tags, key=lambda x: tags.get(x, 0), reverse=True)}
        res = {"word": word, "transcription": data.get("transcription"),"translation": translations, "tags": tags}
        return res

if __name__ == "__main__":
    d = Dictionary()
    print(d.__get_data_from_web("where"))