import '@testing-library/jest-dom';
import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders Hello, Frontend! text", () => {
  render(<App />);
  const headingElement = screen.getByText(/Hello, Frontend!/i);
  expect(headingElement).toBeInTheDocument();
});
