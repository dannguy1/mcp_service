import React from "react";
import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes";
import ErrorBoundary from "./components/ErrorBoundary";

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppRoutes />
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;