import multiprocessing

from typing import Sequence, cast

import click
import numpy as np
import torch
import tqdm

from got10k.datasets import GOT10k
from torch import optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from sot.cfg import TrackerConfig, MODEL_DIR, LOG_DIR, DATASET_DIR
from sot.dataset import SiamesePairwiseDataset
from sot.losses import WeightedBCELoss
from sot.tracker import TrackerSiamFC
from sot.utils import create_ground_truth_mask_and_weight


class SiamFCTrainer:
    def __init__(self, cfg: TrackerConfig) -> None:
        self.cfg: TrackerConfig = cfg
        
        self.device: torch.device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu')
        
        self.tracker: TrackerSiamFC = TrackerSiamFC(cfg, self.device)
        
        response_map_size = (self.cfg.response_size, self.cfg.response_size)
        mask_mat, weight_mat = create_ground_truth_mask_and_weight(
            response_map_size, self.cfg.positive_class_radius,
            self.cfg.total_stride, self.cfg.batch_size)
        self.mask_mat = torch.from_numpy(mask_mat).float().to(self.device)
        weight_mat = torch.from_numpy(weight_mat).float()
        
        self.optimizer = optim.SGD(
            self.tracker.model.parameters(), lr=self.cfg.initial_lr,
            weight_decay=self.cfg.weight_decay, momentum=self.cfg.momentum)
        self.criterion = WeightedBCELoss(weight_mat).to(self.device)
        
        self.lr_scheduler = self.create_exponential_lr_scheduler(
            self.optimizer, self.cfg.initial_lr, self.cfg.ultimate_lr,
            self.cfg.n_epochs)
    
    def run(self) -> None:
        writer = SummaryWriter(LOG_DIR)
        
        pairwise_dataset = self.init_pairwise_dataset()
        n_workers = max(
            1, min(self.cfg.n_workers, multiprocessing.cpu_count() - 1))
        pin_memory = torch.cuda.is_available()
        
        train_loader = DataLoader(
            pairwise_dataset, batch_size=self.cfg.batch_size, shuffle=True,
            num_workers=n_workers, pin_memory=pin_memory, drop_last=True)
        
        self.tracker.model.train()
        
        for epoch in range(1, self.cfg.n_epochs + 1):
            loss = self._run_epoch(epoch, train_loader)
            writer.add_scalar("Loss/train", loss, epoch)
            torch.save(self.tracker.model.state_dict(), MODEL_DIR)
        
        writer.close()
    
    def _run_epoch(self, epoch: int, train_loader: DataLoader) -> float:
        losses_sum = 0.0
        n_batches = len(train_loader)
        
        epoch_text = f"epoch: {epoch}/{self.cfg.n_epochs}"
        
        with tqdm.tqdm(total=n_batches, file=sys.stdout) as pbar:
            for batch, (exemplar, instance) in enumerate(train_loader, start=1):
                exemplar = exemplar.to(self.device)
                instance = instance.to(self.device)
            
                self.optimizer.zero_grad()
                pred_response_maps = self.tracker.model(exemplar, instance)
            
                loss = self.criterion(pred_response_maps, self.mask_mat)
                loss.backward()
                self.optimizer.step()
                
                curr_loss = loss.item()
                losses_sum += curr_loss
                curr_batch_loss = losses_sum / batch
                
                loss_text = f"loss: {curr_loss:.5f} [{curr_batch_loss:.4f}]"
                pbar.set_description(f"{epoch_text} | {loss_text}")
                pbar.update()
        
        self.lr_scheduler.step()
        batch_loss = losses_sum / n_batches
        
        return batch_loss
    
    @staticmethod
    def init_pairwise_dataset() -> SiamesePairwiseDataset:
        data_seq = GOT10k(root_dir=DATASET_DIR, subset='train')
        pairwise_dataset = SiamesePairwiseDataset(
            cast(Sequence, data_seq), TrackerConfig())
        
        return pairwise_dataset
    
    @staticmethod
    def create_exponential_lr_scheduler(
            optimizer, initial_lr: float, ultimate_lr: float,
            n_epochs: int) -> optim.lr_scheduler.ExponentialLR:
        assert n_epochs > 0
        
        # Learning rate is geometrically annealed at each epoch. Starting from
        # A and terminating at B, then the known gamma factor x for n epochs
        # is computed as
        #         A * x ^ n = B,
        #                 x = (B / A)^(1 / n).
        gamma = np.power(ultimate_lr / initial_lr, 1.0 / n_epochs)
        lr_scheduler = optim.lr_scheduler.ExponentialLR(optimizer, gamma)
        
        return lr_scheduler


@click.command()
def main() -> int:
    np.random.seed(731995)
    cfg = TrackerConfig()
    trainer = SiamFCTrainer(cfg)
    trainer.run()
    
    return 0


if __name__ == '__main__':
    import sys
    
    sys.exit(main())
