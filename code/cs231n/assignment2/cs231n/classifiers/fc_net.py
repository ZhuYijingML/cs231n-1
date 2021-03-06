from builtins import range
from builtins import object
import numpy as np

from cs231n.layers import *
from cs231n.layer_utils import *

class TwoLayerNet():
    def __init__(self, input_dim=3*32*32, hidden_dim=100, num_classes=10, weight_scale=1e-3, reg=0.0):
        self.params = {}
        self.reg = reg
        
        self.params['W1'] = weight_scale * np.random.randn(input_dim, hidden_dim)
        self.params['b1'] = np.zeros(hidden_dim)
        self.params['W2'] = weight_scale * np.random.randn(hidden_dim, num_classes)
        self.params['b2'] = np.zeros(num_classes)
    
    def loss(self, X, y=None):
        grads = {}
        
        W1 = self.params['W1']
        b1 = self.params['b1']
        W2 = self.params['W2']
        b2 = self.params['b2']
        
        grads['W1'] = np.zeros_like(W1)
        grads['b1'] = np.zeros_like(b1)
        grads['W2'] = np.zeros_like(W2)
        grads['b2'] = np.zeros_like(b2)
        
        relu_out, cache_relu_out = affine_relu_forward(X, W1, b1)
        scores, cache_out = affine_forward(relu_out, W2, b2)
        
        if y is None:
            return scores
        
        loss, Dscores = softmax_loss(scores, y)
        dx, grads['W2'], grads['b2'] = affine_backward(Dscores, cache_out)
        _, grads['W1'], grads['b1'] = affine_relu_backward(dx, cache_relu_out)
        
        loss += 0.5 * self.reg * (np.sum(W1 * W1) + np.sum(W2 * W2))
        grads['W2'] = grads['W2'] + self.reg * W2
        grads['W1'] = grads['W1'] + self.reg * W1
        return loss, grads
    

class FullyConnectedNet(object):
    def __init__(self, hidden_dims, input_dim=3*32*32, num_classes=10, weight_scale=1e-3, 
                 reg=0.0, dropout=1, normalization=None, dtype=np.float64, seed=None):
        self.normalization = normalization
        self.use_dropout = dropout != 1
        self.reg = reg
        self.num_layers = 1 + len(hidden_dims)
        self.dtype = dtype
        self.params = {}
        self.norm_params = {}
        self.weight_scale = weight_scale
        self.hidden_dims = hidden_dims
        self.dropout = dropout
        self.dropout_params = {}
        
        all_dims = [input_dim] + hidden_dims + [num_classes]
        for i in range(1, self.num_layers + 1):
            in_dim = all_dims[i-1]
            out_dim = all_dims[i]
            w_name = 'W%d' %i
            b_name = 'b%d' %i
            self.params[w_name] = self.weight_scale * np.random.randn(in_dim, out_dim)
            self.params[b_name] = np.zeros(out_dim)

            if i != self.num_layers and self.normalization is not None:
                gamma_name = 'gamma%d' %i
                beta_name = 'beta%d' %i
                self.params[gamma_name] = np.ones(out_dim)
                self.params[beta_name] = np.zeros(out_dim)

                norm_name = 'norm%d' %i
                self.norm_params[norm_name] = {}
                
        if self.use_dropout:
            self.dropout_params['p'] = self.dropout
            if seed is not None:
                self.dropout_params['seed'] = seed
    
    def loss(self, X, y=None):
        loss = 0.0
        total_loss = 0.0
        grads = {}
        caches = {}
        out = X
                
        for i in range(1, self.num_layers + 1):
            w_name = 'W%d' %i
            b_name = 'b%d' %i
            cache_name = 'cache%d' %i
            
            weight = self.params[w_name]
            bias = self.params[b_name]
            total_loss += 0.5 * self.reg * np.sum(weight * weight)
            
            if i != self.num_layers:
                if self.normalization is not None:
                    gamma_name = 'gamma%d' %i
                    beta_name = 'beta%d' %i
                    norm_name = 'norm%d' %i
                    gamma = self.params[gamma_name]
                    beta = self.params[beta_name]
                    norm_param = self.norm_params[norm_name]

                    if self.normalization == 'batch_norm':
                        if y is None:
                            norm_param['mode'] = 'test'
                        else:
                            norm_param['mode'] = 'train'
                        
                    out, caches[cache_name] = affine_norm_relu_forward(out, weight, bias, gamma, beta, 
                                                                           norm_param, norm_type=self.normalization)                 
                else:
                    out, caches[cache_name] = affine_relu_forward(out, weight, bias)
                    
                if self.use_dropout:
                    dropout_cache_name = 'dropout%d' %i
                    if y is None:
                        self.dropout_params['mode'] = 'test'
                    else:
                        self.dropout_params['mode'] = 'train'
                    out, caches[dropout_cache_name] = dropout_forward(out, self.dropout_params)
            else:
                out, caches[cache_name] = affine_forward(out, weight, bias)

        if y is None:
            return out
        
        loss, dout = softmax_loss(out, y)
        total_loss += loss

        for i in range(self.num_layers, 0, -1):
            w_name = 'W%d' %i
            b_name = 'b%d' %i
            cache_name = 'cache%d' %i
            
            weight = self.params[w_name]
            cache = caches[cache_name]
            
            if i != self.num_layers:
                if self.use_dropout:
                    dropout_cache_name = 'dropout%d' %i
                    dropout_cache = caches[dropout_cache_name]
                    dout = dropout_backward(dout, dropout_cache)

                if self.normalization is not None:
                    gamma_name = 'gamma%d' %i
                    beta_name = 'beta%d' %i

                    dout, dw, db, dgamma, dbeta = affine_norm_relu_backward(dout, cache, norm_type=self.normalization)
                    grads[gamma_name] = dgamma
                    grads[beta_name] = dbeta
                else:
                    dout, dw, db = affine_relu_backward(dout, cache)
            else:
                dout, dw, db = affine_backward(dout, cache)

            grads[w_name] = dw + self.reg * weight
            grads[b_name] = db

        return total_loss, grads