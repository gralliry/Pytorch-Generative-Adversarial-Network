# -*- coding: utf-8 -*-
# @Description:
import os

import torch.optim
from torch.utils.tensorboard import SummaryWriter

from torch.utils.data.dataloader import DataLoader
from torchvision import transforms
from torchvision.datasets import CIFAR10
import argparse

from models import *

parser = argparse.ArgumentParser()

parser.add_argument("-e", "--epoch", default=100, type=int, help="Training times")

args = parser.parse_args()


def main():
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    # dataset
    train_datasets = CIFAR10("./datasets", train=True, transform=transform_train)

    test_datasets = CIFAR10("./datasets", train=False, transform=transform_test)

    # dataloader
    train_dataloader = DataLoader(train_datasets, batch_size=256, shuffle=True, num_workers=4)
    test_dataloader = DataLoader(test_datasets, batch_size=256, shuffle=False, num_workers=0)

    # device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # loss function
    loss_fn = nn.CrossEntropyLoss().to(device)

    # network model
    # https://github.com/kuangliu/pytorch-cifar

    # ------------------Select the model to train------------------
    # model = SimpleDLA()
    # model = VGG('VGG19')
    model = ResNet18()
    # model = PreActResNet18()
    # model = GoogLeNet()
    # model = DenseNet121()
    # model = ResNeXt29_2x64d()
    # model = MobileNet()
    # model = MobileNetV2()
    # model = DPN92()
    # model = ShuffleNetG2()
    # model = SENet18()
    # model = ShuffleNetV2(1)
    # model = EfficientNetB0()
    # model = RegNetX_200MF()
    # model = SimpleDLA()

    model = model.to(device)

    # Here you can load the already trained model parameter file to continue training
    model.load_state_dict(torch.load("./parameter/ResNet/train_100_0.9126999974250793.pth", map_location=device))

    model_name = model.__class__.__name__

    # optimizer
    """
    In terms of loss function, SGD(stochastic gradient descent), SGD(stochastic gradient Descent),
    Two optimizers, Adam (Adaptive Moment Estimation) and SGD (Adaptive Moment Estimation), are selected. 
    In practice, SGD stochastic gradient descent is found to be better for the optimization of this experiment.
    """
    # learning rate
    learning_rate = 1e-3
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9, weight_decay=5e-4)
    # use Cosine Annealing to adjust learning rate
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=200)

    # Record training steps
    total_train_step = 0
    total_train_loss = 0

    if not os.path.exists(f"./tensorboard/{model_name}"):
        os.mkdir(f"./tensorboard/{model_name}")
    if not os.path.exists(f"./parameter/{model_name}"):
        os.mkdir(f"./parameter/{model_name}")
    # Training process recorder
    writer = SummaryWriter(f"./tensorboard/{model_name}")
    # The number of training rounds
    for i in range(args.epoch):
        print(f"Epoch {i + 1} start")
        model.train()
        for imgs, targets in train_dataloader:
            imgs, targets = imgs.to(device), targets.to(device)
            output = model(imgs)

            loss = loss_fn(output, targets)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_train_step += 1
            total_train_loss += loss.item()

            if total_train_step % 100 == 0:
                print(f"Train Epoch: {total_train_step}, Loss: {total_train_loss / total_train_step}")
                writer.add_scalar("train_loss", total_train_loss / total_train_step, total_train_step)

        # test
        model.eval()
        total_test_loss = 0

        total_num = 0
        total_accuracy = 0
        with torch.no_grad():
            for imgs, targets in test_dataloader:
                imgs, targets = imgs.to(device), targets.to(device)

                output = model(imgs)

                loss = loss_fn(output, targets)

                total_test_loss += loss.item()
                accuracy = (output.argmax(1) == targets).sum()

                total_num += test_dataloader.batch_size
                total_accuracy += accuracy

        # Record the accuracy and loss of the total train step
        print(f"test loss: {total_test_loss / total_num}")
        writer.add_scalar("test_loss", total_test_loss / total_num, total_train_step)
        print(f"test accuracy: {total_accuracy / total_num}")
        writer.add_scalar("test_accuracy", total_accuracy / total_num, total_train_step)

        # Save the training parameter file
        torch.save(model.state_dict(), f"./parameter/{model_name}/train_{i + 1}_{total_accuracy / total_num}.pth")

        # Adjust learning rate
        scheduler.step()
    # tensorboard --logdir=tensorboard/{model_name} --port=6008
    writer.close()


if __name__ == "__main__":
    main()
