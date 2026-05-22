from .schema import FeedforwardPrediction, load_prediction, save_prediction, save_reconstruct_config

__all__ = [
    "FeedforwardPrediction",
    "load_prediction",
    "save_prediction",
    "save_reconstruct_config",
    "load_reconstruction",
    "load_predictions_file",
    "reconstruct",
    "reconstruct_from_config",
]


def __getattr__(name: str):
    if name == "reconstruct":
        from .reconstruct import reconstruct

        return reconstruct
    if name == "reconstruct_from_config":
        from .reconstruct import reconstruct_from_config

        return reconstruct_from_config
    if name == "load_predictions_file":
        from .visual import load_predictions_file

        return load_predictions_file
    if name == "load_reconstruction":
        from .visual import load_reconstruction

        return load_reconstruction
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
