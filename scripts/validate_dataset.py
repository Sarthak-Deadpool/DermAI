from collections import Counter

from scripts.dermai_dataset import DermAIDataset, CLASS_TO_IDX


for split in ["train", "validation", "test"]:
    dataset = DermAIDataset(split)
    counts = Counter()
    
    print(f"\nChecking {split} split ({len(dataset)} images)...")
    
    for index in range(len(dataset)):
        image, label = dataset[index]
        
        assert tuple(image.shape) == (3 , 224, 224)
        assert image.isfinite().all()
        assert image.min().item() >= 0
        assert image.max().item() <= 1
        
        label_id = label.item()
        assert label_id in CLASS_TO_IDX.values()
        counts[label_id] += 1
        
    print(f"Successfully checked: {sum(counts.values())}/{len(dataset)}")
    print(f"Class counts by index: {dict(sorted(counts.items()))}")

print("\nFull dataset validation passed!")
    