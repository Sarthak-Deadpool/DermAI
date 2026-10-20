import pytest
import torch
import torch.nn.functional as F


from scripts.focal_loss import MulticlassFocalLoss



def test_focal_loss_is_finite_and_nonnegative():
    logits = torch.tensor([[3.0, 0.5, -1.0], [0.2, 2.0, 0.1]])
    targets = torch.tensor([0,1])
    
    loss = MulticlassFocalLoss()(logits, targets)
    
    
    assert torch.isfinite(loss)
    assert loss.item() >= 0 
    
def test_gamma_zero_matches_cross_entropy():
    logits = torch.tensor([[1.0, 2.0, 0.5], [2.5, 0.2, 0.1]])
    targets = torch.tensor([1,0])
    
    focal = MulticlassFocalLoss(gamma=0.0)(logits, targets)
    cross_entropy = F.cross_entropy(logits, targets)
    
    assert torch.allclose(focal, cross_entropy)
    
def test_focal_loss_supports_backpropagation():
    logits = torch.rand(4, 6, requires_grad=True)
    targets = torch.tensor([0, 1, 2, 5])
    
    loss = MulticlassFocalLoss()(logits, targets)
    loss.backward()
    
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()
    
def test_none_reduction_returns_per_sample_losses():
    logits =  torch.randn(3, 6)
    targets = torch.tensor([0,2,5])
    
    losses = MulticlassFocalLoss(reduction="none")(logits, targets)
    
    assert losses.shape == (3,)
    
def test_invalid_reduction_is_rejected():
    with pytest.raises(ValueError):
        MulticlassFocalLoss(reduction="invalid")