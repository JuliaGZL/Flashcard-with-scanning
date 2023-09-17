import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from textblob import TextBlob
import re
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize
import math
from typing import List
from wordnik import WordApi, swagger
import urllib

class Scanner:
    def __init__(self):
        # Set threshold constants
        self.S_LOWER_THRESH = 50
        self.V_LOWER_THRESH = 100
        self.COLOR_D_THRESH = 300

        self.api_url = 'http://api.wordnik.com/v4'
        self.api_key = 'rvxqbsjdgv3mhg7wbn6jvy3xvihzxf7vwepyp2bl38gjzl27u'
        self.client = swagger.ApiClient(self.api_key, self.api_url)

    # Increases the contrast of hue and value
    @staticmethod
    def read_img(path) -> cv2.Mat:
        return cv2.imread(path)

    @staticmethod
    def get_color(hsv_image, y, x) -> np.ndarray:
        return hsv_image[y, x]

    # Returns mask of all highlights by intensity and OTSU
    @staticmethod
    def get_highlight_mask(hsv_image) -> cv2.Mat:
        # Increase contrast of value
        hsv_image[:, :, 2] = cv2.equalizeHist(hsv_image[:, :, 2])

        # Calculates grayscale image based on intensity difference
        rows, cols = hsv_image.shape[:2]
        grayscale = np.zeros((rows, cols), np.uint8)
        for y in range(rows):
            for x in range(cols):
                pixel = hsv_image[y][x]
                max_intensity = max(pixel[0], pixel[1], pixel[2])
                min_intensity = min(pixel[0], pixel[1], pixel[2])
                grayscale[y][x] = max_intensity - min_intensity

        # OTSU Threshold
        threshold_val, thresh_img = cv2.threshold(
            grayscale, 0, 255, cv2.THRESH_OTSU)
        return thresh_img

    @staticmethod
    def get_color_mask(hsv_image, color: np.ndarray, h_thresh=5, s_thresh=50, v_thresh=50) -> cv2.Mat:
        c0 = int(color[0])
        c1 = int(color[1])
        c2 = int(color[2])
        color_mask = cv2.inRange(
            hsv_image, (c0-h_thresh, c1-s_thresh, c2-v_thresh), (c0+h_thresh, c1+s_thresh, c2+v_thresh))
        return color_mask

    ''' Returns words and locations in left, top, width and height'''

    @staticmethod
    def scan_words(image: cv2.Mat) -> dict:
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result = pytesseract.image_to_data(
            gray_image, output_type=Output.DICT)
        words = result['text']
        locations = dict((i, result[i])
                         for i in ['left', 'top', 'width', 'height'])
        return words, locations

    ''' region list has [left, top, width, height]si '''

    @staticmethod
    def is_highlight(mask, region, limit=0.3) -> bool:
        mask_region = mask[region[1]:region[1] +
                           region[3], region[0]:region[0]+region[2]]
        highlight_count = np.count_nonzero(mask_region > 0)
        highlight_ratio = highlight_count / (region[2]*region[3])
        if highlight_ratio > limit:
            return True
        else:
            return False

    # Returns words filtered by highlight mask
    def filter_scanned_words(self, highlight_mask, color1_mask, color2_mask, words: list, regions: dict, limit=0.3) -> list:
        terms = [[]]
        definitions = [[]]
        term_count = 0
        def_count = 0
        for i, word in enumerate(words):
            region = [regions['left'][i], regions['top'][i],
                      regions['width'][i], regions['height'][i]]
            if self.is_highlight(highlight_mask, region, limit):
                if self.is_highlight(color1_mask, region, limit):
                    if term_count > 3:
                        terms.append([])
                    terms[-1].append(word)
                    term_count = 0
                    def_count += 1
                elif self.is_highlight(color2_mask, region, limit):
                    if def_count > 3:
                        definitions.append([])
                    definitions[-1].append(word)
                    def_count = 0
                    term_count += 1
                else:
                    term_count += 1
                    def_count += 1
        return terms, definitions

    def modify_all_grammar(self, word_list: list) -> list:
        texts = []
        for sentence in word_list:
            modified = self.modify_grammar(sentence)
            if modified != "":
                texts.append(self.modify_grammar(sentence))
        return texts

    # Returns string after modifying to correct grammar using TextBlob library
    def modify_grammar(self, sentence: list) -> str:
        str_sentence = ""
        for word in sentence:
            if word.replace(" ", "") != "":
                str_sentence = str_sentence + word + " "
        textblob_sentence = TextBlob(str_sentence)
        corrected_text = textblob_sentence.correct()
        return str(corrected_text)

    def remove_chars(self, string: str, kept_chars="") -> str:
        chars = re.escape(kept_chars)
        removed = re.sub(f"[^\\w\\s{chars}]", '', string)
        return removed

    def clean_list_chars(self, strings: list, kept_chars="") -> list:
        for i, string in enumerate(strings):
            strings[i] = self.remove_chars(string, kept_chars)
        return strings

    # Removes unnecessary whitespaces and characters for terms
    def clean_all_terms(self, terms) -> List[str]:
        for i, term in enumerate(terms):
            terms[i] = self.remove_chars(term)
            if term.endswith(" "):
                terms[i] = terms[i][:-1]
        output_terms = []
        for term in terms:
            if term.replace(" ", "") != "":
                output_terms.append(term)
        return output_terms

    def clean_all_defs(self, definitions) -> List[str]:
        for i, definition in enumerate(definitions):
            if definition.endswith(" "):
                definitions[i] = definition[:-1]
        output_defs = []
        for definition in definitions:
            if definition.replace(" ", "") != "":
                output_defs.append(definition)
        return output_defs

    def pair_words(self, corrected_terms, corrected_defs):
        if len(corrected_terms) == len(corrected_defs):
            return corrected_terms, corrected_defs
        else:
            print("Length are not the same!")

    def get_cvt_type(self, tag):  # Probably useless
        if tag.startswith('J'):
            return wordnet.ADJ
        elif tag.startswith('V'):
            return wordnet.VERB
        elif tag.startswith('N'):
            return wordnet.NOUN
        elif tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    def clean_string(self, string: str, mode="l") -> List[str]:
        # Lowercase text
        string = string.lower()
        # Remove numbers and punctuation
        string = re.sub(r"[^a-zA-Z' -]+", '', string)
        # Remove stopwords and tokenize
        stop_words = set(stopwords.words("english"))
        tokens = word_tokenize(string)
        filtered_tokens = []
        for token in tokens:
            if token not in stop_words:
                filtered_tokens.append(token)
        # Lemmatizing tokens
        if mode == "l":
            lemmatizer = WordNetLemmatizer()
            for i, token in enumerate(filtered_tokens):
                filtered_tokens[i] = lemmatizer.lemmatize(
                    token)
        elif mode == "s":
            stemmer = PorterStemmer()
            for i, token in enumerate(filtered_tokens):
                filtered_tokens[i] = stemmer.stem(token)
        else:
            print("Unknown mode! Please check your input parameters.")
        return filtered_tokens

    @staticmethod
    def get_synonyms(token: str) -> set:
        synonyms = set()
        synsets = wordnet.synsets(token)
        for synset in synsets:
            synonym_list = synset.lemma_names()
            for synonym in synonym_list:
                synonyms.add(synonym)
        return synonyms

    @staticmethod
    def get_tokens_synonyms(tokens: list) -> dict:
        output_synonyms = {}
        for token in tokens:
            output_synonyms[token] = []
            synsets = wordnet.synsets(token)
            for synset in synsets:
                synonym_list = synset.lemma_names()
                for synonym in synonym_list:
                    output_synonyms[token].append(synonym)
        return output_synonyms

    # Get definitions from Wordnik API
    def get_defs(self, word: str) -> List[str]:
        word_api = WordApi.WordApi(self.client)
        try:
            def_objects = word_api.getDefinitions(word, limit=10)
        except urllib.error.HTTPError:
            return None
        definitions = []
        for def_object in def_objects:
            text = def_object.text
            # Ignore None objects
            if text:
                text = self._remove_brackets(text)
                definitions.append(text)
        return definitions
    
    # Removes <> and content inside <>
    def _remove_brackets(self, text: str) -> str:
        text = re.sub("\<.*?\>", "", text)
        return text
        
    # Returns a dictionary of suggested definitions, where key is definition and value is similarity
    def suggest_def(self, term: str, definition: str, limit=0.5) -> dict:
        if term.replace(" ", "") != "":
            term = term.replace("\n", "")
            # 1. Clean the inputed definition
            cleaned_user_tokens = self.clean_string(definition)
            # 2. Get definitions
            definitions = self.get_defs(term)
            dict_defs = {}
            zero_count = 0
            if definitions:
                for defin in definitions:
                    # 3. Clean definitions
                    def_tokens = self.clean_string(defin)
                    def_set = SynonymSet(def_tokens)
                    similarity = def_set.calc_jaccard_similarity(
                        cleaned_user_tokens)
                    if similarity < 0.00001:
                        zero_count += 1
                        dict_defs[defin] = 0
                    else:
                        dict_defs[defin] = similarity
                dict_defs = sorted(dict_defs.items(),
                                key=lambda kv: (kv[1], kv[0]), reverse=True)
            else:
                return None
            print(dict_defs)
            return dict_defs
        else:
            return None

    # Shows image by cv2 imshow
    def show_image(self, image) -> None:
        cv2.imshow("Image", image)
        cv2.waitKey(0)

    # (Connected with GUI) function to scan cleaned results from a single image
    def scan_image(self, path, hsv_term: tuple, hsv_def: tuple, mask_limit=0.1) -> List[str]:
        image = self.read_img(path)
        hsv_term = np.array(hsv_term)
        hsv_def = np.array(hsv_def)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        highlight_mask = self.get_highlight_mask(hsv_image)
        term_mask = self.get_color_mask(hsv_image, hsv_term)
        def_mask = self.get_color_mask(hsv_image, hsv_def)
        words, locations = self.scan_words(image)
        terms, definitions = self.filter_scanned_words(
            highlight_mask, term_mask, def_mask, words, locations, mask_limit)
        corrected_terms = self.modify_all_grammar(terms)
        corrected_terms = self.clean_all_terms(corrected_terms)
        corrected_defs = self.modify_all_grammar(definitions)
        corrected_defs = self.clean_all_defs(corrected_defs)
        return corrected_terms, corrected_defs
        ''' TODO: 不要把没有的term去掉了！ '''
        ''' TODO: remove 符号 and leave option to keep 符号 '''
        ''' TODO: Clean the structure of code before adjusting the jaccard similarity algorithm '''
        ''' TODO: Jaccard similarity algorithm (adding union and intersection by jaro winklet instead of
        directly comparing 1) '''


class SynonymSet:
    def __init__(self, words: list) -> None:
        self.words_synonyms = Scanner.get_tokens_synonyms(words)
        self.words = {}
        for word in words:
            self.words[word] = False

    def add(self, word) -> None:
        self.words_synonyms[word] = Scanner.get_synonyms(word)

    def remove(self, word) -> None:
        del self.words[word]
        del self.words_synonyms[word]

    def contains(self, word, jaro_limit=0.8, scale=0.1) -> bool:
        for compare_word in self.words_synonyms.keys():
            if self.calc_jaro_winkler_similarity(word, compare_word, scale) > jaro_limit:
                return True, compare_word
            for synonym in self.words_synonyms[compare_word]:
                if self.calc_jaro_winkler_similarity(word, synonym, scale) > jaro_limit:
                    return True, compare_word
        return False, None

    # Where unions and intersections also include those within jaro limit
    def count_union_and_intersection(self, tokens: list, jaro_limit=0.8, scale=0.1) -> int:
        user_tokens = {}
        union_count = 0
        intersect_count = 0
        for token in tokens:
            user_tokens[token] = False
        for token in tokens:
            exists, word = self.contains(token, jaro_limit, scale)
            if exists:
                user_tokens[token] = True
                self.words[word] = True
        for exists in user_tokens.values():
            if exists:
                union_count += 1
                intersect_count += 1
            else:
                union_count += 1
        for exists in self.words.values():
            if not exists:
                union_count += 1
        return union_count, intersect_count

    # Returns Jaccard similarity
    def calc_jaccard_similarity(self, tokens) -> float:
        union_count, intersect_count = self.count_union_and_intersection(
            tokens)
        return intersect_count / union_count

    @staticmethod
    def calc_jaro_similarity(word1, word2) -> float:
        if word1 == word2:
            return 1.0
        len1 = len(word1)
        len2 = len(word2)
        max_distance = math.floor(max(len1, len2)/2) - 1
        matches = 0
        transpositions = 0
        word1_matched = [False] * len1
        word2_matched = [False] * len2

        # Number of matches
        for index1, letter in enumerate(word1):
            for index2 in range(max(0, index1-max_distance), min(len2, index1+max_distance+1)):
                if letter == word2[index2] and not word2_matched[index2]:
                    matches += 1
                    word1_matched[index1] = True
                    word2_matched[index2] = True
                    break

        # Number of transpositions
        index2 = 0
        for index1, letter in enumerate(word1):
            if word1_matched[index1]:
                while not word2_matched[index2]:
                    index2 += 1
                if letter != word2[index2]:
                    transpositions += 1
                index2 += 1

        transpositions /= 2
        if matches != 0:
            return (matches/len1 + matches/len2 + (matches-transpositions)/matches)/3
        else:
            return 0

    def calc_jaro_winkler_similarity(self, word1, word2, scaling_factor=0.1) -> float:
        jaro_similarity = self.calc_jaro_similarity(word1, word2)
        # Get the number of same starting letters
        start_count = 0
        idx = 0
        while (start_count < 4 and idx < min(len(word1), len(word2))):
            if word1[idx] == word2[idx]:
                start_count += 1
                idx += 1
            else:
                break
        return jaro_similarity + scaling_factor * start_count * (1-jaro_similarity)


if __name__ == "__main__":
    path = "/Users/juliag/Desktop/sample6.jpg"
    s = Scanner()
