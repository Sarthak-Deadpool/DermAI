
from pathlib import Path
import json
import random

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import resnet18, ResNet18_Weights

from scripts.dermai_dataset import (
    CLASS_TO_IDX,
    DEFAULT_MANIFEST,
    DermAIDataset,
)
from scripts.focal_loss import MulticlassFocalLoss


# --------------------------------------------------
# 1. Experiment configuration
# --------------------------------------------------

SEED = 42
BATCH_SIZE = 16
NUM_WORKERS = 0

EPOCHS = 10
PATIENCE = 3

BACKBONE_LEARNING_RATE = 1e-5
HEAD_LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

FOCAL_GAMMA = 2.0

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_DIR = PROJECT_ROOT / "models" / "checkpoints"
REPORT_DIR = PROJECT_ROOT / "reports" / "finetune_focal"

CHECKPOINT_PATH = (
    CHECKPOINT_DIR / "resnet18_finetune_focal.pt"
)

CLASS_NAMES = [
    name
    for name, index in sorted(
        CLASS_TO_IDX.items(),
        key=lambda item: item[1],
    )
]

# ImageNet normalization for pretrained ResNet18.
MEAN = torch.tensor(
    [0.485, 0.456, 0.406]
).view(1, 3, 1, 1)

STD = torch.tensor(
    [0.229, 0.224, 0.225]
).view(1, 3, 1, 1)


# --------------------------------------------------
# 2. Reproducibility
# --------------------------------------------------

def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# --------------------------------------------------
# 3. Classification metrics
# --------------------------------------------------

def calculate_metrics(
    targets: list[int],
    predictions: list[int],
) -> dict:
    num_classes = len(CLASS_NAMES)

    confusion = torch.zeros(
        num_classes,
        num_classes,
        dtype=torch.int64,
    )

    for target, prediction in zip(targets, predictions):
        confusion[target, prediction] += 1

    per_class = {}
    f1_values = []
    recalls = []

    for index, name in enumerate(CLASS_NAMES):
        tp = int(confusion[index, index])
        actual = int(confusion[index, :].sum())
        predicted_count = int(confusion[:, index].sum())

        fp = predicted_count - tp
        fn = actual - tp

        precision = (
            tp / (tp + fp)
            if tp + fp
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn
            else 0.0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        per_class[name] = {
            "support": actual,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

        f1_values.append(f1)
        recalls.append(recall)

    total = int(confusion.sum())

    accuracy = (
        sum(
            int(confusion[i, i])
            for i in range(num_classes)
        ) / total
        if total
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "macro_f1": sum(f1_values) / num_classes,
        "balanced_accuracy": sum(recalls) / num_classes,
        "per_class": per_class,
        "confusion_matrix": confusion.tolist(),
    }


# --------------------------------------------------
# 4. One training or validation epoch
# --------------------------------------------------

def run_epoch(
    model,
    loader,
    criterion,
    optimizer,
    device,
    training: bool,
) -> dict:
    model.train(training)

    total_loss = 0.0
    targets_all = []
    predictions_all = []

    context = (
        torch.enable_grad()
        if training
        else torch.no_grad()
    )

    with context:
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)

            # Normalize images for pretrained ResNet18.
            images = (
                images - MEAN.to(device)
            ) / STD.to(device)

            if training:
                optimizer.zero_grad(set_to_none=True)

            logits = model(images)
            loss = criterion(logits, targets)

            if training:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)

            predictions = logits.argmax(dim=1)

            targets_all.extend(targets.cpu().tolist())
            predictions_all.extend(
                predictions.cpu().tolist()
            )

    metrics = calculate_metrics(
        targets_all,
        predictions_all,
    )

    metrics["loss"] = (
        total_loss / len(loader.dataset)
    )

    return metrics


# --------------------------------------------------
# 5. Main experiment
# --------------------------------------------------

def main() -> None:
    set_seed(SEED)

    # Keep the same CPU setup as the earlier experiments.
    device = torch.device("cpu")

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Device: {device}")
    print(f"Classes: {CLASS_NAMES}")
    print("Loading dataset splits...")

    # The dataset enables augmentation for training only.
    train_dataset = DermAIDataset("train")
    val_dataset = DermAIDataset("validation")

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        generator=torch.Generator().manual_seed(SEED),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
    )

    # --------------------------------------------------
    # 6. Verify training class counts
    # --------------------------------------------------

    manifest = pd.read_csv(DEFAULT_MANIFEST)

    train_rows = manifest[
        manifest["split"] == "train"
    ]

    counts = (
        train_rows["diagnostic"]
        .value_counts()
        .reindex(CLASS_NAMES, fill_value=0)
    )

    if (counts == 0).any():
        raise ValueError(
            "A class has no training examples."
        )

    print(
        "Training class counts:",
        counts.to_dict(),
    )

    print(
        "Loss: unweighted multiclass focal loss"
    )
    print(f"Focal gamma: {FOCAL_GAMMA}")
    print("Weighted sampling: disabled")
    print("Training augmentation: enabled")

    # --------------------------------------------------
    # 7. Load and configure ResNet18
    # --------------------------------------------------

    print("Loading ImageNet-pretrained ResNet18...")

    model = resnet18(
        weights=ResNet18_Weights.DEFAULT
    )

    # Freeze the existing backbone first.
    for parameter in model.parameters():
        parameter.requires_grad = False

    # Fine-tune the final residual block.
    for parameter in model.layer4.parameters():
        parameter.requires_grad = True

    # Replace the classifier for our six dataset classes.
    model.fc = nn.Linear(
        model.fc.in_features,
        len(CLASS_NAMES),
    )

    model = model.to(device)

    trainable_names = [
        name
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]

    print("\nTrainable parameters:")
    for name in trainable_names:
        print(f"  {name}")

    assert trainable_names, (
        "No trainable parameters were found."
    )

    assert all(
        name.startswith("layer4.")
        or name.startswith("fc.")
        for name in trainable_names
    ), "Unexpected trainable parameters detected."

    assert any(
        name.startswith("layer4.")
        for name in trainable_names
    ), "layer4 is not trainable."

    assert any(
        name.startswith("fc.")
        for name in trainable_names
    ), "Classification head is not trainable."

    # --------------------------------------------------
    # 8. Focal loss and optimizer
    # --------------------------------------------------

    criterion = MulticlassFocalLoss(
        gamma=FOCAL_GAMMA,
        reduction="mean",
    )

    optimizer = torch.optim.AdamW(
        [
            {
                "params": list(
                    model.layer4.parameters()
                ),
                "lr": BACKBONE_LEARNING_RATE,
            },
            {
                "params": list(
                    model.fc.parameters()
                ),
                "lr": HEAD_LEARNING_RATE,
            },
        ],
        weight_decay=WEIGHT_DECAY,
    )

    # --------------------------------------------------
    # 9. Training loop and early stopping
    # --------------------------------------------------

    best_macro_f1 = -1.0
    best_epoch = 0
    epochs_without_improvement = 0
    history = []

    for epoch in range(1, EPOCHS + 1):
        train_metrics = run_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
            training=True,
        )

        val_metrics = run_epoch(
            model,
            val_loader,
            criterion,
            optimizer,
            device,
            training=False,
        )

        record = {
            "epoch": epoch,
            "train_loss": train_metrics["loss"],
            "train_accuracy": train_metrics["accuracy"],
            "train_macro_f1": train_metrics["macro_f1"],
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_balanced_accuracy": (
                val_metrics["balanced_accuracy"]
            ),
        }

        history.append(record)

        print(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"train loss {train_metrics['loss']:.4f} | "
            f"train acc {train_metrics['accuracy']:.4f} | "
            f"val loss {val_metrics['loss']:.4f} | "
            f"val acc {val_metrics['accuracy']:.4f} | "
            f"val macro-F1 {val_metrics['macro_f1']:.4f}"
        )

        # Select the best model by validation macro-F1.
        if val_metrics["macro_f1"] > best_macro_f1:
            best_macro_f1 = val_metrics["macro_f1"]
            best_epoch = epoch
            epochs_without_improvement = 0

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_to_idx": CLASS_TO_IDX,
                    "class_names": CLASS_NAMES,
                    "epoch": epoch,
                    "val_macro_f1": best_macro_f1,
                    "seed": SEED,
                    "normalization_mean": (
                        MEAN.flatten().tolist()
                    ),
                    "normalization_std": (
                        STD.flatten().tolist()
                    ),
                    "training_mode": (
                        "layer4 and classification head fine-tuned"
                    ),
                    "loss_function": "MulticlassFocalLoss",
                    "focal_gamma": FOCAL_GAMMA,
                    "class_weighting": False,
                    "weighted_sampling": False,
                    "training_augmentation": True,
                },
                CHECKPOINT_PATH,
            )

            print(
                f"  Saved best checkpoint: "
                f"{CHECKPOINT_PATH}"
            )

        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= PATIENCE:
            print(
                "Early stopping: validation macro-F1 "
                "did not improve."
            )
            break

    # --------------------------------------------------
    # 10. Reload best checkpoint and evaluate validation
    # --------------------------------------------------

    checkpoint = torch.load(
        CHECKPOINT_PATH,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    best_val_metrics = run_epoch(
        model,
        val_loader,
        criterion,
        optimizer,
        device,
        training=False,
    )

    # Save epoch-by-epoch history.
    pd.DataFrame(history).to_csv(
        REPORT_DIR / "training_history.csv",
        index=False,
    )

    # Save experiment configuration and final metrics.
    report = {
        "experiment": "ResNet18 fine-tuning with focal loss",
        "best_epoch": best_epoch,
        "best_validation_metrics": best_val_metrics,
        "class_names": CLASS_NAMES,
        "training_class_counts": counts.to_dict(),
        "seed": SEED,
        "batch_size": BATCH_SIZE,
        "backbone_learning_rate": BACKBONE_LEARNING_RATE,
        "head_learning_rate": HEAD_LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "epochs_requested": EPOCHS,
        "patience": PATIENCE,
        "pretrained_weights": "ResNet18 ImageNet DEFAULT",
        "training_mode": (
            "layer4 and classification head fine-tuned"
        ),
        "loss_function": "MulticlassFocalLoss",
        "focal_gamma": FOCAL_GAMMA,
        "class_weighting": False,
        "weighted_sampling": False,
        "training_augmentation": True,
        "device": str(device),
    }

    with open(
        REPORT_DIR / "validation_metrics.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print("\nFocal-loss experiment complete.")
    print(f"Best epoch: {best_epoch}")
    print(
        f"Best validation macro-F1: "
        f"{best_macro_f1:.4f}"
    )
    print(
        f"Best validation accuracy: "
        f"{best_val_metrics['accuracy']:.4f}"
    )
    print(
        f"Best validation balanced accuracy: "
        f"{best_val_metrics['balanced_accuracy']:.4f}"
    )
    print(f"Checkpoint: {CHECKPOINT_PATH}")
    print(f"Reports: {REPORT_DIR}")


if __name__ == "__main__":
    main()
