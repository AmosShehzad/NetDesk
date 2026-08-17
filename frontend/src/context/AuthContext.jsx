import { createContext, useContext, useState } from 'react';
import client from '../api/client';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const login = async (reg_number, password) => {
  const res = await client.post('/users/login/', { reg_number, password });
  localStorage.setItem('access', res.data.access);
  localStorage.setItem('refresh', res.data.refresh);
  const profile = await client.get('/users/profile/');
  setUser(profile.data);
  return profile.data;
};

  const register = async (phone_number, username, password) => {
    await client.post('/users/register/', { phone_number, username, password });
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);