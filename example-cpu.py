# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the GNU General Public License version 3.

from typing import Tuple
import os
import sys
import torch
import fire
import time
import json
from pathlib import Path
from llama import ModelArgs, Transformer, Tokenizer, LLaMA


def load(
        ckpt_dir: str,
        tokenizer_path: str,
        max_seq_len: int,
        max_batch_size: int,
) -> LLaMA:
    start_time = time.time()
    checkpoints = sorted(Path(ckpt_dir).glob("*.pth"))
    ckpt_path = checkpoints[-1]

    print("Loading model...")
    checkpoint = torch.load(ckpt_path, map_location="cpu")
    with open(Path(ckpt_dir) / "params.json", "r") as f:
        params = json.loads(f.read())

    model_args: ModelArgs = ModelArgs(
        max_seq_len=max_seq_len, max_batch_size=max_batch_size, **params
    )

    tokenizer = Tokenizer(model_path=tokenizer_path)

    model_args.vocab_size = tokenizer.n_words

    model = Transformer(model_args)
    model.to("cpu")
    model.load_state_dict(checkpoint, strict=False)

    generator = LLaMA(model, tokenizer)
    print(f"Loaded model in {time.time() - start_time:.2f} seconds")
    return generator


def main(
        ckpt_dir: str = './model',
        tokenizer_path: str = './tokenizer/tokenizer.model',
        temperature: float = 0.8,
        top_p: float = 0.95,
        max_seq_len: int = 2048,
        max_batch_size: int = 32,
):
    # torch.manual_seed(1)
    # torch.set_default_dtype(torch.bfloat16)

    generator = load(ckpt_dir, tokenizer_path, max_seq_len, max_batch_size)

    prompts = [
        ##### For these prompts, the expected answer is the natural continuation of the prompt #####

        "I believe the meaning of life is",
        # "Simply put, the theory of relativity states that ",
        # "Building a website can be done in 10 simple steps:\n",

        ##### Few shot prompts: https://huggingface.co/blog/few-shot-learning-gpt-neo-and-inference-api #####

        #         """Tweet: "I hate it when my phone battery dies."
        # Sentiment: Negative
        # ###
        # Tweet: "My day has been 👍"
        # Sentiment: Positive
        # ###
        # Tweet: "This is the link to the article"
        # Sentiment: Neutral
        # ###
        # Tweet: "This new music video was incredibile"
        # Sentiment:""",

        #         """Translate English to French:
        # sea otter => loutre de mer
        # peppermint => menthe poivrée
        # plush girafe => girafe peluche
        # cheese =>""",
    ]

    start_time = time.time()

    results = generator.generate(
        prompts, max_gen_len=256, temperature=temperature, top_p=top_p
    )

    for result in results:
        print(result)
        print("\n==================================")

    print(f"Inference took {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    fire.Fire(main)
