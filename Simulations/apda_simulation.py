import numpy as np

class DynamicEnvironment:
    def __init__(self):
        self.g = 9.81
        self.mass = 1.0
        
    def get_acceleration(self, position, thrust, current_time):
        a_known = (thrust / self.mass) - self.g
        hidden_force = 15.0 * np.exp(-3.0 * position) if position > 0 else 0
        if current_time >= 4.0:
            hidden_force -= 12.0  # Environmental microburst anomaly
        return a_known + (hidden_force / self.mass), hidden_force

class AdvancedAdaptiveAdapter:
    def __init__(self):
        self.g = 9.81
        self.mass = 1.0
        self.w1 = np.random.randn(1, 8) * 0.1
        self.b1 = np.zeros((1, 8))
        self.w2 = np.random.randn(8, 1) * 0.1
        self.b2 = np.zeros((1, 1))
        self.history_buffer = []
        self.npu_active = True       
        self.learning_rate = 0.1     
        self.error_threshold = 0.2   
        
    def npu_predict(self, position):
        h = np.maximum(0, np.dot(position, self.w1) + self.b1)
        return np.dot(h, self.w2)[0, 0] + self.b2[0, 0]

    def calculate_control(self, current_pos, target_pos, velocity):
        error = target_pos - current_pos
        kp, kd = 15.0, 5.0
        base_calculus_thrust = (self.g * self.mass) + (kp * error) - (kd * velocity)
        npu_compensation = self.npu_predict(np.array([[current_pos]])) if self.npu_active else 0.0
        return np.clip(base_calculus_thrust - npu_compensation, 0.0, 40.0)

    def monitor_and_adapt(self, position, observed_acceleration, thrust):
        expected_accel = (thrust / self.mass) - self.g
        perceived_residual = observed_acceleration - expected_accel
        current_npu_guess = self.npu_predict(np.array([[position]])) if self.npu_active else 0.0
        prediction_error = abs(perceived_residual - current_npu_guess)
        
        if prediction_error > self.error_threshold and not self.npu_active:
            self.npu_active = True
            self.learning_rate = 0.2 
            print(f"\n[ALERT] Exception! Residual: {prediction_error:.4f} | WAKING NPU | LR: {self.learning_rate}")
        elif prediction_error <= (self.error_threshold * 0.2) and self.npu_active and len(self.history_buffer) > 20:
            self.npu_active = False
            print(f"\n[INFO] Converged. Residual: {prediction_error:.4f} | HIBERNATING NPU (Power-Save)")
            
        if self.npu_active:
            self.history_buffer.append((position, perceived_residual))
            if len(self.history_buffer) > 60: self.history_buffer.pop(0)
            if prediction_error < self.error_threshold:
                self.learning_rate = max(0.01, self.learning_rate * 0.95)
                
            if len(self.history_buffer) >= 10:
                for _ in range(8):
                    idx = np.random.randint(0, len(self.history_buffer))
                    pos_past, target_residual = self.history_buffer[idx]
                    x = np.array([[pos_past]]); h_input = np.dot(x, self.w1) + self.b1
                    h = np.maximum(0, h_input); pred = np.dot(h, self.w2) + self.b2
                    loss_deriv = 2 * (pred - target_residual)
                    dw2 = np.dot(h.T, loss_deriv); db2 = loss_deriv
                    dh = np.dot(loss_deriv, self.w2.T); dh[h_input <= 0] = 0
                    self.w1 -= self.learning_rate * np.dot(x.T, dh)
                    self.b1 -= self.learning_rate * dh
                    self.w2 -= self.learning_rate * dw2
                    self.b2 -= self.learning_rate * db2

if __name__ == "__main__":
    env = DynamicEnvironment()
    adapter = AdvancedAdaptiveAdapter()
    dt = 0.01; position = 2.5; velocity = 0.0; target_altitude = 0.5
    print(f"{'Time (s)':<10}{'Position (m)':<15}{'NPU Status':<20}{'Learning Rate'}")
    print("-" * 60)
    for step in range(700):
        current_time = step * dt
        if step == 400: position = 0.15
        thrust = adapter.calculate_control(position, target_altitude, velocity)
        actual_accel, _ = env.get_acceleration(position, thrust, current_time)
        velocity += actual_accel * dt; position += velocity * dt
        adapter.monitor_and_adapt(position, actual_accel, thrust)
        if step % 50 == 0 or step in [401, 410, 450]:
            status_str = "ACTIVE (Learning)" if adapter.npu_active else "HIBERNATING (Sleep)"
            print(f"{current_time:<10.2f}{position:<15.4f}{status_str:<20}{adapter.learning_rate:.4f}")
