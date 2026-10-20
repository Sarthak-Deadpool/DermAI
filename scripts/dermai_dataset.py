from pathlib import Path

import pandas as pd
import torch
import random

from torchvision.transforms import ColorJitter
from torch.utils.data import Dataset
from torchvision.transforms import functional as TF


from backend.app.services.image_preprocessing import preprocess_image



PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = PROJECT_ROOT / "datasets" / "split_manifest.csv"
DEFAULT_IMAGE_ROOT = PROJECT_ROOT / "datasets" / "zr7vgbcyr2-1" / "images"

CLASS_TO_IDX = {
    "ACK": 0,
    "BCC": 1,
    "MEL": 2,
    "NEV": 3,
    "SCC": 4,
    "SEK": 5,
}

VALID_SPLITS = {"train", "validation", "test"}


def validate_manifest(manifest: pd.DataFrame) -> None:
    required_columns = {
        "img_id",
        "patient_id",
        "diagnostic",
        "split",
    }
    
    missing = required_columns - set(manifest.columns)
    
    if missing:
        raise ValueError(
            f"Manifest is missing columns: {sorted(missing)}"
        )
        
    if manifest.empty:
         raise ValueError("Manifest contains no records")
     
    if manifest[list(required_columns)].isnull().any().any():
        raise ValueError("Required manifest fields contain missing values")
    
    unknown_labels = set(manifest["diagnostic"]) - set(CLASS_TO_IDX)
    
    if unknown_labels:
        raise ValueError(
             f"Unknown diagnostic labels: {sorted(unknown_labels)}"
        )
        
        
    unknown_splits = set(manifest["split"]) - VALID_SPLITS
    
    if unknown_splits:
        raise ValueError(
            f"Unknown dataset splits: {sorted(unknown_splits)}"
        )
        
    if manifest["img_id"].duplicated().any():
        raise ValueError("Manifest contains duplicate image IDs")
    
    patient_splits = manifest.groupby("patient_id")["split"].nunique()
    if(patient_splits>1).any():
        raise ValueError("Patient leakage detected between dataset splits")
    
    
    
class DermAIDataset(Dataset):
    def __init__(
        self,
        split: str,
        manifest_path: str | Path = DEFAULT_MANIFEST,
        image_root: str | Path = DEFAULT_IMAGE_ROOT,
        augment: bool | None = None,
    ) -> None:
        if split not in VALID_SPLITS:
            raise ValueError(f"Invalid split: {split}")
        
        self.image_root = Path(image_root)
        if not self.image_root.is_dir():
                raise FileNotFoundError(
            f"Image directory not found: {self.image_root}"
            )
                
        manifest_path = Path(manifest_path)
        if not manifest_path.is_file():
                raise FileNotFoundError(
            f"Manifest not found: {manifest_path}"
            )
                
        manifest = pd.read_csv(manifest_path)
        validate_manifest(manifest)
        
        
        self.records = (
            manifest.loc[manifest["split"] == split]
            .reset_index(drop=True)
        )
        
        self.split = split
        
        self.augment = (split == "train") if augment is None else augment
        
        if self.augment and split != "train":
            raise ValueError("Augmentation is allowed only for the training split.")
        
        if self.records.empty:
                raise ValueError(f"No records found for split: {split}")
            
            
        self.image_path = []
        for image_id in self.records["img_id"] :
            matches = list(self.image_root.rglob(str(image_id)))
            if len(matches) != 1:
                raise ValueError(
                    f"Expected exactly one image for {image_id}, "
                    f"found {len(matches)}"
                )
                
            self.image_path.append(matches[0])
            
    def __len__(self) -> int:
        return len(self.records)
    
    def __getitem__(self, index:int) -> tuple[torch.Tensor, torch.Tensor]:
        row  = self.records.iloc[index]
        image_path = self.image_path[index]
        
        image_array = preprocess_image(image_path, size=(224,224))
        
        image = torch.from_numpy(image_array).permute(2, 0, 1).contiguous()
        
        if self.augment:
            if random.random() < 0.5:
                image = TF.hflip(image)
                
                
            angle = random.uniform(-15.0, 15.0)
            image = TF.rotate(
                image,
                angle=angle,
                interpolation= TF.InterpolationMode.BILINEAR,
            )
            
            image = ColorJitter(
                brightness=0.10,
                contrast=0.10,
            )(image)
            
            image = image.clamp(0.0, 1.0)
            
        
        label = CLASS_TO_IDX[row["diagnostic"]]
        target = torch.tensor(label, dtype=torch.long)
        
        return image, target
        
        