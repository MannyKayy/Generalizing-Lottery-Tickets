from utils import *
from dataloader import *
from model import *
from parser import *
import torch
import random
import torchvision
import torch.optim as optim

def train(model, dataloader, architecture, optimizer_type, device, models_dir):
	"""
	Function to train the network 

	Arguments
	---------
	model : the PyTorch neural network model to be trained
	dataloader : PyTorch dataloader for loading the dataset
	architecture : The neural network architecture (VGG19 or ResNet50)
	optimizer_type : The optimizer to use for training (SGD / Adam)
	device : Device(GPU/CPU) on which to perform computation
	model_path: Path to directory where trained model/checkpoints will be saved

	Returns
	-------
	None
	"""
	if architecture == "vgg19":
		num_epochs = 160
		lr_anneal_epochs = [80, 120]
	elif architecture == "resnet50":
		num_epochs = 90
		lr_anneal_epochs = [50, 65, 80]
	else:
		raise ValueError(architecture + " architecture not supported")

	criterion = nn.CrossEntropyLoss().cuda()
	if optimizer_type == 'sgd':
		optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=0.0001)
	elif optimizer_type == 'adam':
		optimizer = optim.Adam(model.parameters(), lr=0.0003, weight_decay=0.0001)
	else:
		raise ValueError(optimizer_type + " optimizer not supported")

	if architecture == "vgg19":
		model.apply(initialize_xavier_normal)

	model.to(device)

	print(f"Started Training...")
	for epoch in range(1, num_epochs+1):
		if epoch in lr_anneal_epochs:
			optimizer.param_groups[0]['lr'] /= 10

		for batch_num, data in enumerate(dataloader, 0):
			inputs, labels = data[0].to(device), data[1].to(device)

			optimizer.zero_grad()
			outputs = model(inputs)
			loss = criterion(outputs, labels)
			loss.backward()
			optimizer.step()

		if epoch <=5 or epoch%(num_epochs/10) == 0:
			try:
				torch.save({'epoch': epoch,'model_state_dict': model.state_dict(),'optimizer_state_dict': optimizer.state_dict()}, models_dir + f"/{epoch}")
			except FileNotFoundError:
				print(models_dir + " path not found")
		print(f"Epoch {epoch} : Loss = {loss.item()}")
	print("Finished Training!")


if __name__ == '__main__':
	#Parsers the command line arguments
	parser = args_parser_train()
	args = parser.parse_args()

	#Sets random seed
	random.seed(args.seed)

	#Uses GPU is available
	device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
	print(f'Using {device} device.')

	#Loads dataset
	dataloader = load_dataset(args.dataset, args.batch_size, True)

	#Checks number of classes to aa appropriate linear layer at end of model
	if args.dataset in ['cifar10', 'fashionmnist', 'svhn']:
		num_classes = 10
	elif args.dataset in ['cifar100']:
		num_classes = 100
	else:
		raise ValueError(args.dataset + " dataset not supported")

	#Loads model
	model = load_model(args.architecture, num_classes)

	train(model, dataloader, args.architecture, args.optimizer, device, args.model_saving_path)


