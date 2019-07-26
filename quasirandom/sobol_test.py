# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python2, python3
"""Tests for google3.area120.nomisma.tensorflow.qmc.sobol."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp

from nomisma_quant_finance.quasirandom import sobol
from tensorflow.python.framework import test_util  # pylint: disable=g-direct-tensorflow-import


@test_util.run_all_in_graph_and_eager_modes
class SampleSobolSequenceTest(tf.test.TestCase):

  def test_known_values_small_dimension(self):
    # The first five elements of the non-randomized Sobol sequence
    # with dimension 2
    sample = sobol.sample(2, 5)
    # These are in the original order, not Gray code order.
    expected = np.array([[0.5, 0.5], [0.25, 0.75], [0.75, 0.25], [0.125, 0.625],
                         [0.625, 0.125]],
                        dtype=np.float32)
    self.assertAllClose(expected, self.evaluate(sample), rtol=1e-6)

  def test_more_known_values(self):
    # The first 31 elements of the non-randomized Sobol sequence
    # with dimension 5
    sample = sobol.sample(5, 31)
    # These are in the Gray code order.
    expected = [[0.5, 0.5, 0.5, 0.5, 0.5], [0.75, 0.25, 0.25, 0.25, 0.75],
                [0.25, 0.75, 0.75, 0.75, 0.25],
                [0.375, 0.375, 0.625, 0.875, 0.375],
                [0.875, 0.875, 0.125, 0.375, 0.875],
                [0.625, 0.125, 0.875, 0.625, 0.625],
                [0.125, 0.625, 0.375, 0.125, 0.125],
                [0.1875, 0.3125, 0.9375, 0.4375, 0.5625],
                [0.6875, 0.8125, 0.4375, 0.9375, 0.0625],
                [0.9375, 0.0625, 0.6875, 0.1875, 0.3125],
                [0.4375, 0.5625, 0.1875, 0.6875, 0.8125],
                [0.3125, 0.1875, 0.3125, 0.5625, 0.9375],
                [0.8125, 0.6875, 0.8125, 0.0625, 0.4375],
                [0.5625, 0.4375, 0.0625, 0.8125, 0.1875],
                [0.0625, 0.9375, 0.5625, 0.3125, 0.6875],
                [0.09375, 0.46875, 0.46875, 0.65625, 0.28125],
                [0.59375, 0.96875, 0.96875, 0.15625, 0.78125],
                [0.84375, 0.21875, 0.21875, 0.90625, 0.53125],
                [0.34375, 0.71875, 0.71875, 0.40625, 0.03125],
                [0.46875, 0.09375, 0.84375, 0.28125, 0.15625],
                [0.96875, 0.59375, 0.34375, 0.78125, 0.65625],
                [0.71875, 0.34375, 0.59375, 0.03125, 0.90625],
                [0.21875, 0.84375, 0.09375, 0.53125, 0.40625],
                [0.15625, 0.15625, 0.53125, 0.84375, 0.84375],
                [0.65625, 0.65625, 0.03125, 0.34375, 0.34375],
                [0.90625, 0.40625, 0.78125, 0.59375, 0.09375],
                [0.40625, 0.90625, 0.28125, 0.09375, 0.59375],
                [0.28125, 0.28125, 0.15625, 0.21875, 0.71875],
                [0.78125, 0.78125, 0.65625, 0.71875, 0.21875],
                [0.53125, 0.03125, 0.40625, 0.46875, 0.46875],
                [0.03125, 0.53125, 0.90625, 0.96875, 0.96875]]
    # Because sobol.sample computes points in the original order,
    # not Gray code order, we ignore the order and only check that the sets of
    # rows are equal.
    self.assertAllClose(
        sorted(tuple(row) for row in expected),
        sorted(tuple(row) for row in self.evaluate(sample)),
        rtol=1e-6)

  def test_skip(self):
    dim = 10
    n = 50
    skip = 17
    sample_noskip = sobol.sample(dim, n + skip)
    sample_skip = sobol.sample(dim, n, skip)

    self.assertAllClose(
        self.evaluate(sample_noskip[skip:, :]), self.evaluate(sample_skip))

  def test_normal_integral_mean_and_var_correctly_estimated(self):
    n = int(1000)
    # This test is almost identical to the similarly named test in
    # monte_carlo_test.py. The only difference is that we use the Sobol
    # samples instead of the random samples to evaluate the expectations.
    # MC with pseudo random numbers converges at the rate of 1/ Sqrt(N)
    # (N=number of samples). For QMC in low dimensions, the expected convergence
    # rate is ~ 1/N. Hence we should only need 1e3 samples as compared to the
    # 1e6 samples used in the pseudo-random monte carlo.
    mu_p = tf.constant([-1., 1.], dtype=tf.float64)
    mu_q = tf.constant([0., 0.], dtype=tf.float64)
    sigma_p = tf.constant([0.5, 0.5], dtype=tf.float64)
    sigma_q = tf.constant([1., 1.], dtype=tf.float64)
    p = tfp.distributions.Normal(loc=mu_p, scale=sigma_p)
    q = tfp.distributions.Normal(loc=mu_q, scale=sigma_q)

    cdf_sample = sobol.sample(2, n)
    q_sample = q.quantile(cdf_sample)

    # Compute E_p[X].
    e_x = tf.contrib.bayesflow.monte_carlo.expectation_importance_sampler(
        f=lambda x: x, log_p=p.log_prob, sampling_dist_q=q, z=q_sample, seed=42)

    # Compute E_p[X^2].
    e_x2 = tf.contrib.bayesflow.monte_carlo.expectation_importance_sampler(
        f=tf.square, log_p=p.log_prob, sampling_dist_q=q, z=q_sample, seed=1412)

    stddev = tf.sqrt(e_x2 - tf.square(e_x))
    # Keep the tolerance levels the same as in monte_carlo_test.py.
    self.assertEqual(p.batch_shape, e_x.shape)
    self.assertAllClose(self.evaluate(p.mean()), self.evaluate(e_x), rtol=0.01)
    self.assertAllClose(
        self.evaluate(p.stddev()), self.evaluate(stddev), rtol=0.02)

  def test_two_dimensional_projection(self):
    # This test fails for Halton sequences, where two-dimensional projections of
    # high dimensional samples are perfectly correlated. So with Halton samples,
    # the integral below is incorrecly computed to be 1/3 rather than the
    # correct 1/4.
    dim = 170
    n = 1000
    sample = sobol.sample(dim, n)
    x = self.evaluate(sample[:, dim - 2])
    y = self.evaluate(sample[:, dim - 1])
    corr = np.corrcoef(x, y)[1, 0]
    self.assertAllClose(corr, 0.0, atol=0.05)
    self.assertAllClose((x * y).mean(), 0.25, rtol=0.05)


if __name__ == '__main__':
  tf.test.main()
