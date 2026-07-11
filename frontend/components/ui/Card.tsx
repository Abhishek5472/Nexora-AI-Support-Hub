import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function Card({ children, className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-neutral-200 bg-white p-6 shadow-md transition-all duration-300 hover:shadow-lg dark:border-neutral-800 dark:bg-neutral-900/60 dark:backdrop-blur-md ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
