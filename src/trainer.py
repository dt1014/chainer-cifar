import numpy as np
import six

from chainer import functions as F
from chainer import cuda
from chainer import Variable

class CifarTrainer(object):
    def __init__(self, net, optimizer, epoch_num=100, batch_size=100, device_id=-1):
        self.net = net
        self.optimizer = optimizer
        self.epoch_num = epoch_num
        self.batch_size = batch_size
        self.device_id = device_id
        if device_id >= 0:
            self.xp = cuda.cupy
            self.net.to_gpu(device_id)
        else:
            self.xp = np

    def fit(self, x, y, test_x=None, test_y=None, callback=None):
        if self.device_id >= 0:
            with cuda.cupy.cuda.Device(self.device_id):
                return self.__fit(x, y, test_x, test_y, callback)
        else:
            return self.__fit(x, y, test_x, test_y, callback)

    def __fit(self, x, y, test_x, test_y, callback):
        batch_size = self.batch_size
        for epoch in six.moves.range(self.epoch_num):
            perm = np.random.permutation(len(x))
            train_loss = 0
            train_acc = 0
            for i in six.moves.range(0, len(x), self.batch_size):
                self.net.zerograds()
                batch_index = perm[i:i + batch_size]
                x_batch = self.__trans_image(x[batch_index])
                loss, acc = self.__forward(x_batch, y[batch_index])
                loss.backward()
                self.optimizer.update()
                train_loss += float(loss.data) * len(x_batch)
                train_acc += float(acc.data) * len(x_batch)
            train_loss /= len(x)
            train_acc /= len(x)
            test_loss = 0
            test_acc = 0
            if test_x is not None and test_y is not None:
                for i in six.moves.range(0, len(test_x), self.batch_size):
                    x_batch = self.__crop_image(test_x[i:i + batch_size])
                    loss, acc = self.__forward(x_batch, test_y[i:i + batch_size], train=False)
                    test_loss += float(loss.data) * len(x_batch)
                    test_acc += float(acc.data) * len(x_batch)
                test_loss /= len(test_x)
                test_acc /= len(test_x)
            if callback is not None:
                callback(epoch, self.net, self.optimizer, train_loss, train_acc, test_loss, test_acc)

    def __forward(self, batch_x, batch_t, train=True):
        xp = self.xp
        x = Variable(xp.asarray(batch_x), volatile=not train)
        t = Variable(xp.asarray(batch_t), volatile=not train)
        y = self.net(x, train=train)
        loss = F.softmax_cross_entropy(y, t)
        acc = F.accuracy(y, t)
        return loss, acc

    def __trans_image(self, x):
        return x[:,:,2:30,2:30]

    def __crop_image(self, x):
        return x[:,:,2:30,2:30]