from helpers import *
import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt

class Experiment():
  """ One experiment on neuron crash, contains a fixed weights network """
  def __init__(self, N, P, KLips, do_print = False):
    """ Initialize using given number of neurons per layer N (array), probability of failure P, and the Lipschitz coefficient """
    
    if do_print:
      print('Creating network for %d-dimensional input and %d-dimensional output, with %d hidden layers' % (N[0], N[-1], len(N) - 2))
    
    # saving N
    self.N = N
    
    # making list if P is a number
    if type(P) == float:
      P = [P] * (len(N) - 2)
      
    # checking if the length is correct. Last and first layers cannot have failures so P is shorter than N
    assert(len(N) == len(P) + 2)
      
    # saving P, last layer has zero probability of failure
    self.P = P + [0.0]
    
    # maximal value of output from neuron (1 since using sigmoid)
    self.C = 1.
    
    # saving K
    self.K = KLips
    
  def predict_no_dropout(self, data):
    """ Get correct network output for a given input vector """
    return self.model_no_dropout.predict(np.array([data]))[0]
  
  def predict(self, data, repetitions = 100):
    """ Get crashed network outputs for given input vector and number of repetitions """
    data = np.repeat(np.array([data]), repetitions, axis = 0)
    return self.model.predict(data)
  
  def plot_error(experiment, errors):
    """ Plot the histogram of error  """
    
    # plotting
    plt.title('Network error histogram plot')
    plt.xlabel('Network output error')
    plt.ylabel('Frequency')
    plt.hist(errors, density = True)
    #plt.plot([true, true], [0, 1], label = 'True value')
    #plt.legend()
    plt.show()
  
  def get_error(experiment, inp, repetitions = 100):
    """ Return error between crashed and correct networks """
    return experiment.predict(inp, repetitions = repetitions) - experiment.predict_no_dropout(inp)
  
  def get_wb(self, layer):
    """ Get weight and bias matrix """
    return np.vstack((self.W[layer], self.B[layer]))
  
  def get_max_f(self, layer, func):
    """ Maximize func(weights) over neurons in layer """
    wb = self.get_wb(layer)
    res = [func(w_neuron) for w_neuron in wb.T]
    return np.max(res)
  
  def get_max_f_xy(self, layer, func, same_only = False):
    """ Maximize func(w1, w2) over neurons in layer """
    wb = self.get_wb(layer)
    if same_only: res = [func(w_neuron, w_neuron) for w_neuron in wb.T]
    else: res = [func(w_neuron1, w_neuron2) for w_neuron1 in wb.T for w_neuron2 in wb.T]
    return np.max(res)
  
  def get_mean_std_error(self):
    """ Get theoretical bound for mean and std of error given weights """
    
    # Expectation of error
    EDelta = 0.
    
    # Expectation of error squared
    EDelta2 = 0.
    
    # Array of expectations
    EDeltaArr = [0]
    
    # Array of expectations of squares
    EDelta2Arr = [0]
    
    # Loop over layers
    for layer in range(len(self.W)):
      is_last = layer + 1 == len(self.W)
      
      # probability of failure of a single neuron
      p_l = self.P[layer]
      
      # maximal 1-norm of weights
      w_1_norm = self.get_max_f(layer, norm1)
      
      # alpha from article for layer
      alpha = self.get_max_f_xy(layer, dot_abs, same_only = is_last)
      
      # beta from article for layer
      beta = self.get_max_f_xy(layer, norm1_minus_dot_abs, same_only = is_last)
      
      # a, b from article for EDelta2 (note that old EDelta is used)
      a = self.C ** 2 * p_l * (alpha + p_l * beta) + 2 * self.K * self.C * p_l * (1 - p_l) * beta * EDelta
      b = self.K ** 2 * (1 - p_l) * (alpha + (1 - p_l) * beta)
      
      # Updating EDelta2
      EDelta2 = a + b * EDelta2
      
      # Updating EDelta
      EDelta = p_l * w_1_norm * self.C + self.K * w_1_norm * (1 - p_l) * EDelta
      
      # Adding new values to arrays
      EDeltaArr.append(EDelta)
      EDelta2Arr.append(EDelta2)
      
    # Debug output
    #print(EDeltaArr)
    #print(EDelta2Arr)
    
    # Returning mean and sqrt(std^2)
    return EDelta, EDelta2 ** 0.5
  
  def run(self, repetitions = 10000, inputs = 50, do_plot = True, do_print = True, do_tqdm = True):
    """ Run a single experiment with a fixed network """

    # Creating input data
    data = self.get_inputs(inputs)

    # Computing true values
    trues = [self.predict_no_dropout(value) for value in data]

    # Running the experiment
    tqdm_ = tqdm if do_tqdm else (lambda x : x)
    errors = [self.get_error(value, repetitions = repetitions) for value in tqdm_(data)]
    
    # Computing Maximal Absolute Mean/Std Error over 
    errors_abs = np.max(np.abs(errors), axis = 2)
    means = np.mean(errors_abs, axis = 1)
    stds = np.std(errors_abs, axis = 1)
    mean_exp = np.max(means)
    std_exp = np.max(stds)

    # Computing bound values
    mean_bound, std_bound = self.get_mean_std_error()

    # Plotting the error histogram
    if do_plot:
      self.plot_error(np.array(errors).reshape(-1))

    # Printing results summary
    if do_print:
      print('Error; maximal over inputs, average over dropout:')
      print('True values array mean: %f variance %f' % (np.mean(trues), np.std(trues)))
      print('Experiment %f Std %f' % (mean_exp, std_exp))
      print('Equation   %f Std %f' % (mean_bound, std_bound))
      print('Tightness  %.1f%% Std %.1f%%' % (100 * mean_exp / mean_bound, 100 * std_exp / std_bound))

    # Returning summary
    return mean_exp, std_exp, mean_bound, std_bound, np.std(trues)
