import React, { createContext, useContext, useState, ReactNode } from "react";
import { setAuthToken } from "@/services/api";

type PortalRole = "admin" | "trainee";

interface PortalContextType {
  role: PortalRole;
  setRole: (role: PortalRole) => void;
  userName: string;
  userEmail: string;
  isAuthenticated: boolean;
  setIsAuthenticated: (v: boolean) => void;
  logout: () => void;
}

const PortalContext = createContext<PortalContextType>({
  role: "admin",
  setRole: () => {},
  userName: "Super Admin",
  userEmail: "admin@corp.com",
  isAuthenticated: false,
  setIsAuthenticated: () => {},
  logout: () => {},
});

export const usePortal = () => useContext(PortalContext);

export const PortalProvider = ({ children }: { children: ReactNode }) => {
  const [role, setRole] = useState<PortalRole>("admin");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const userName = role === "admin" ? "Super Admin" : "John Doe";
  const userEmail = role === "admin" ? "admin@corp.com" : "john@corp.com";

  const logout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
    setRole("admin");
  };

  return (
    <PortalContext.Provider value={{ role, setRole, userName, userEmail, isAuthenticated, setIsAuthenticated, logout }}>
      {children}
    </PortalContext.Provider>
  );
};
