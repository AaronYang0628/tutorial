import torch
from PIL import Image
import timm
import numpy as np
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform


class FeatureExtractor:
    def __init__(self, modelname):
        # Try to load the pre-trained model. If downloading weights fails (no internet
        # or hub access), fall back to an uninitialized model to keep the service running.
        try:
            # Load the pre-trained model (may download weights from HF/timm hub)
            self.model = timm.create_model(
                modelname, pretrained=True, num_classes=0, global_pool="avg"
            )
        except Exception as e:
            # Fallback: create the model without pretrained weights. This avoids
            # crashing the app if the container has no outbound network access.
            print(f"Warning: failed to load pretrained weights for {modelname}: {e}\n"
                  "Falling back to uninitialized model (pretrained=False).")
            self.model = timm.create_model(
                modelname, pretrained=False, num_classes=0, global_pool="avg"
            )
        self.model.eval()

        # Get the input size required by the model
        self.input_size = self.model.default_cfg["input_size"]

        config = resolve_data_config({}, model=modelname)
        # Get the preprocessing function provided by TIMM for the model
        self.preprocess = create_transform(**config)

    def __call__(self, imagepath):
        # Preprocess the input image
        input_image = Image.open(imagepath).convert("RGB")  # Convert to RGB if needed
        input_image = self.preprocess(input_image)

        # Convert the image to a PyTorch tensor and add a batch dimension
        input_tensor = input_image.unsqueeze(0)

        # Perform inference
        with torch.no_grad():
            output = self.model(input_tensor)

        # Extract the feature vector
        feature_vector = output.squeeze().numpy()

        # L2-normalize using numpy to avoid scikit-learn dependency
        vec = feature_vector.reshape(-1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec
