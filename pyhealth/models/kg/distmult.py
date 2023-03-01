from.kg_base import KGEBaseModel
from pyhealth.datasets import SampleBaseDataset
import torch


class DistMult(KGEBaseModel):
    """ DistMult

    Paper: Yang, B., Yih, W.T., He, X., Gao, J. and Deng, L. Embedding entities and 
    relations for learning and inference in knowledge bases. ICLR 2015.

    """
    def __init__(
        self, 
        dataset: SampleBaseDataset, 
        e_dim: int = 300, 
        r_dim: int = 300, 
        ns: str = "adv", 
        gamma: float = 24.0, 
        use_subsampling_weight: bool = False, 
        use_regularization: str = 'l3',
        mode: str = "multiclass",
        ):
        super().__init__(dataset, e_dim, r_dim, ns, gamma, use_subsampling_weight, use_regularization, mode)
    

    def regularization(self, sample_batch, mode='pos'):
        head, relation, tail = self.data_process(sample_batch, mode)
        reg = (torch.mean(head ** 2) + torch.mean(tail ** 2) + torch.mean(relation ** 2)) / 3
        return reg


    def l3_regularization(self):
        reg_l3 = self.E_emb.norm(p=3) **3 + self.R_emb.norm(p=3) **3
        return reg_l3


    def calc(self, sample_batch, mode='pos'):
        head, relation, tail = self.data_process(sample_batch, mode)

        if mode == 'head':
            score = head * (relation * tail)
        else:
            score = (head * relation) * tail

        score = score.sum(dim=2)
        return score


if __name__ == "__main__":
    from pyhealth.datasets import SampleKGDataset

    samples = [
        {
            'triple': (0, 0, 2835),
            'ground_truth_head': [1027, 1293, 5264, 1564, 7416, 6434, 2610, 4094, 2717, 5007, 5277, 5949, 0, 6870, 6029],
            'ground_truth_tail': [398, 244, 3872, 3053, 1711, 2835, 1348, 2309],
            'subsampling_weight': torch.tensor([0.1857])
        },
        {
            'triple': (4, 2, 6502),
            'ground_truth_head': [4, 69, 1470, 505, 3069],
            'ground_truth_tail': [2517, 907, 4859, 5209, 3680, 273, 6502, 1810, 875, 1794, 1070, 192, 3079, 1420, 5649, 4779, 2348, 4991, 2714, 3202, 120, 1942, 259, 1617, 3203, 292, 1585, 2691, 1512, 2187, 2000, 1935, 5863, 2277, 1635, 4912, 2261, 1367, 2286, 2782, 3750, 6157, 2864, 1506, 4507, 1669, 4044, 1336, 3239, 881, 3264, 2841, 410, 1329, 4029, 1752, 1362, 1216],
            'subsampling_weight': torch.tensor([0.1204])
        },
    ]

    # dataset
    dataset = SampleKGDataset(samples=samples, dataset_name="test")

    # data loader
    from pyhealth.datasets import get_dataloader

    train_loader = get_dataloader(dataset, batch_size=2, shuffle=True)

    # model
    model = DistMult(
        dataset=dataset,
        e_dim=600, 
        r_dim=600, 
    )

    # data batch
    data_batch = next(iter(train_loader))

    # try the model
    ret = model(**data_batch)
    print(ret)

    # try loss backward
    ret["loss"].backward()