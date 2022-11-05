from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
import nltk
import os

nltk.download('stopwords')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def build_vocabulary(training_data_path, training_data_name):
    dataframe = pd.read_csv(os.path.join(BASE_DIR, training_data_path, training_data_name))
    train_iterator = list(zip(dataframe['text'], dataframe['label']))
    tokenizer = get_tokenizer("basic_english")

    def tokenizer_fn(data_iterator):
        for text, _ in data_iterator:
            yield tokenizer(text)

    vocab = build_vocab_from_iterator(tokenizer_fn(train_iterator), specials=["<unk>"])
    vocab.set_default_index(vocab["<unk>"])

    return vocab, tokenizer


def clean_text(dataframe):
    stop_words = list(set(stopwords.words('english')))
    dataframe['text'] = dataframe['text'].apply(lambda x: x.lower())
    dataframe['text'] = dataframe['text'].apply(lambda x: x.replace(r'[^\w\s]', ''))
    dataframe['text'] = dataframe['text'].apply(
        lambda x: ' '.join([word for word in x.split() if word not in stop_words]))

    return dataframe


def tokenize_text(dataframe, vocab, tokenizer):
    dataframe["text"] = dataframe["text"].apply(lambda x: np.array(vocab(tokenizer(x))))
    dataframe['seq_len'] = dataframe['text'].apply(lambda x: len(x))
    percentiles = [i * 0.1 for i in range(10)] + [.95, .99, .995]
    buckets = np.quantile(dataframe['seq_len'], percentiles)
    bucket_labels = [i for i in range(len(buckets) - 1)]
    dataframe['bucket'] = pd.cut(dataframe['seq_len'], bins=buckets, labels=bucket_labels)
    dataframe["seq_len"] = dataframe["seq_len"].astype(int)

    return dataframe[['text', 'label', "seq_len", "bucket"]]