import numpy as np
from math import sqrt, atan2, cos, sin, pi
from filterpy.kalman import KalmanFilter

class IMUProcessor:
    def __init__(self):
        self.theta_gyro = 0.0
        self.phi_gyro = 0.0
        self.psi_gyro = 0.0
        self.theta_complementary = 0.0
        self.phi_complementary = 0.0
        self.psi_complementary = 0.0
        self.heading0 = 0.0
        self.alpha = 0.05

        # Kalman Filter initialization
        self.kf = KalmanFilter(dim_x=6, dim_z=6)
        self.kf.x = np.array([[0.],    # theta
                [0.],    # phi
                [0.],     # psi
                [0.],     # w_theta
                [0.],     # w_phi
                [0.]])   # w_psi
        
        self.kf.H = np.array([[1., 0., 0., 0., 0., 0.],
                [0., 1., 0., 0., 0., 0.],
                [0., 0., 1., 0., 0., 0.],   
                [0., 0., 0., 1., 0., 0.],
                [0., 0., 0., 0., 1., 0.],
                [0., 0., 0., 0., 0., 1.]])
        
        self.kf.P *= 10.
        self.kf.R = 5 * np.eye(6)
        self.kf.Q = 0.005 * np.eye(6)

    def get_angular_position_and_speed(self, sample, delta_t):
        accX = sample[0]
        accY = sample[1]
        accZ = sample[2]
        gyroX = sample[3]
        gyroY = sample[4]
        gyroZ = sample[5]
        mX = sample[6]
        mY = sample[7]
        mZ = sample[8]

        theta_gyro = self.theta_gyro
        phi_gyro = self.phi_gyro
        psi_gyro = self.psi_gyro
        theta_complementary = self.theta_complementary
        phi_complementary = self.phi_complementary
        psi_complementary = self.psi_complementary
        
        accMagnitude = sqrt(accX*accX + accY*accY + accZ*accZ)
        accX = accX / accMagnitude
        accY = accY / accMagnitude
        
        # complementary filter
        theta_acc = atan2(accY, sqrt(accX * accX + accZ * accZ)) * 180 / pi
        phi_acc = -atan2(accX, sqrt(accY * accY + accZ * accZ)) * 180 / pi
        
        theta_gyro += gyroX * delta_t
        phi_gyro += gyroY * delta_t
        psi_gyro += gyroZ * delta_t
        
        alpha = self.alpha
        theta_complementary = alpha * theta_acc + (1 - alpha) * (theta_complementary + gyroX * delta_t)
        phi_complementary = alpha * phi_acc + (1 - alpha) * (phi_complementary + gyroY * delta_t)
        
        Bx = mX * cos(-phi_complementary * pi / 180) - mY * sin(theta_complementary * pi / 180) * mZ * sin(-phi_complementary * pi / 180) + mZ * cos(theta_complementary * pi / 180) * sin(-phi_complementary * pi / 180)
        By = mY * cos(theta_complementary * pi / 180) + mZ * sin(theta_complementary * pi / 180)
        
        psi_mag = atan2(By, Bx) * 180.0 / pi
        
        try:
            psi_mag = psi_mag - self.heading0
        except Exception as e:
            self.heading0 = psi_mag
            psi_mag = 0
        
        psi_complementary = alpha * psi_mag + (1 - alpha) * (psi_complementary + gyroZ * delta_t)
        
        self.theta_complementary = theta_complementary
        self.phi_complementary = phi_complementary
        self.psi_complementary = psi_complementary
        self.theta_gyro = theta_gyro
        self.phi_gyro = phi_gyro
        self.psi_gyro = psi_gyro

        sample.extend([theta_acc, phi_acc, theta_gyro, phi_gyro, psi_gyro, psi_mag, theta_complementary, phi_complementary, psi_complementary])

        self.kf.F = np.array([
            [1., 0., 0., delta_t, 0., 0.],
            [0., 1., 0., 0., delta_t, 0.],
            [0., 0., 1., 0., 0., delta_t],     
            [0., 0., 0., 1., 0., 0.],
            [0., 0., 0., 0., 1., 0.],
            [0., 0., 0., 0., 0., 1.]
        ])
        
        z = np.array([
            [theta_acc],
            [phi_acc],
            [psi_mag],
            [gyroX],
            [gyroY],
            [gyroZ]
        ])
                    
        self.kf.predict()
        self.kf.update(z)
        
        return sample + self.kf.x.flatten().tolist()