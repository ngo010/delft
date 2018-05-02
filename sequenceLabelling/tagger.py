from collections import defaultdict
import numpy as np
import datetime
from sequenceLabelling.metrics import get_entities
from sequenceLabelling.metrics import get_entities_with_offsets
from sequenceLabelling.tokenizer import tokenizeAndFilter

class Tagger(object):

    def __init__(self, model, preprocessor=None):
        self.model = model
        self.preprocessor = preprocessor

    def predict(self, tokens):
        length = np.array([len(tokens)])
        X = self.preprocessor.transform([tokens])
        pred = self.model.predict(X, length)

        return pred

    def tag(self, texts, output_format):
        assert isinstance(texts, list)

        if output_format is 'json':
            res = {
                "software": "DeLFT",
                "date": datetime.datetime.now().isoformat(),
                "model": self.model.config.model_name,
                "texts": []
            }
        else:
           list_of_tags = []

        for text in texts:
            tokens, offsets = tokenizeAndFilter(text)

            pred = self.predict(tokens)
            tags = self._get_tags(pred)
            prob = self._get_prob(pred)
            #entities = self._build_response(tokens, tags, prob)
            
            if output_format is 'json':
                piece = {}
                piece["text"] = text
                piece["entities"] = self._build_json_response(tokens, tags, prob, offsets)["entities"]
                res["texts"].append(piece)
            else:
                the_tags = list(zip(tokens, tags))
                list_of_tags.append(the_tags)

        if output_format is 'json':
            return res
        else:
            return list_of_tags

    def _get_tags(self, pred):
        pred = np.argmax(pred, -1)
        tags = self.preprocessor.inverse_transform(pred[0])

        return tags

    def _get_prob(self, pred):
        prob = np.max(pred, -1)[0]

        return prob

    def _build_json_response(self, tokens, tags, prob, offsets):
        res = {
            "entities": []
        }
        chunks = get_entities_with_offsets(tags, offsets)
        for chunk_type, chunk_start, chunk_end, pos_start, pos_end in chunks:
            # TODO: get the original string rather than regenerating it from tokens
            entity = {
                "text": ' '.join(tokens[chunk_start: chunk_end]),
                "class": chunk_type,
                "score": float(np.average(prob[chunk_start: chunk_end])),
                "beginOffset": pos_start,
                "endOffset": pos_end
            }
            res["entities"].append(entity)

        return res

