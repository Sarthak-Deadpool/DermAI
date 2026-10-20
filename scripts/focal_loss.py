import torch
import torch.nn as nn
import torch.nn.functional as F


class MulticlassFocalLoss(nn.Module):
    
    def __init__(self, gamma: float = 2.0, reduction: str = "mean"):
        super().__init__()
        
        if gamma < 0:
            raise ValueError("gamma must be >= 0")
        
        if reduction not in {"mean", "sum", "none"}:
            raise ValueError(
                "reductio must be 'mean', 'sum' or 'none' "
            )
            
        self.gamma = gamma
        self.reduction = reduction
        
    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        
        if logits.ndim != 2:
            raise ValueError("logits must have shape [batch_size, num_classes]")

        if targets.ndim != 1:
            raise ValueError("targets must have shape [batch_size]")
        
        if logits.shape[0] != targets.shape[0]:
            raise ValueError("logits and targets batch sizes must match")
        
        ce_loss = F.cross_entropy(logits, targets, reduction = "none")
        
        true_class_probability = torch.exp(-ce_loss)
        
        focal_factor = (1.0 -true_class_probability) ** self.gamma
        loss = focal_factor * ce_loss
        
        if self.reduction == "mean":
            return loss.mean()
        
        if self.reduction == "sum":
            return loss.sum()
        
        return loss
        