#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Milan Ondrasovic <milan.ondrasovic@gmail.com>

import sys
import click

import torch


@click.command()
@click.argument("checkpoint_file_path", type=click.Path(exists=True))
@click.argument("model_output_file_path", type=click.Path())
def main(checkpoint_file_path, model_output_file_path):
    """
    Extracts the saved model in a checkpoint given by the CHECKPOINT_FILE_PATH
    as a separate MODEL_OUTPUT_FILE_PATH so that it can be loaded directly.
    """
    checkpoint = torch.load(checkpoint_file_path)
    model_state = checkpoint['model']
    torch.save(model_state, model_output_file_path)


if __name__ == '__main__':
    sys.exit(main())
