"""Download and verify the public model before starting the timed API worker."""

from neuraldebugger.weights import base_directory


if __name__ == "__main__":
    print("Verified base model and tokenizer in", base_directory())
