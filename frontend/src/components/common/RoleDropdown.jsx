/** @format */

import { useEffect, useRef, useState } from "react";

export default function RoleDropdown({
  id = "role",
  name = "role",
  value,
  onChange,
  options,
  required = true,
}) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  const selectedOption = options.find((option) => option.value === value);

  useEffect(() => {
    function handleOutsideClick(event) {
      if (!dropdownRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  return (
    <div ref={dropdownRef} className="relative w-full">
      <input type="hidden" name={name} value={value} required={required} />

      <button
        id={id}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((previous) => !previous)}
        className={`flex w-full items-center justify-between rounded-xl border bg-white px-4 py-3 text-left text-sm font-medium text-slate-800 shadow-sm transition-all duration-200 ${
          open
            ? "border-cyan-600 ring-4 ring-cyan-600/10"
            : "border-slate-200 hover:border-slate-300"
        }`}
      >
        <span>{selectedOption?.label ?? "Select a role"}</span>

        <svg
          className={`h-5 w-5 text-slate-500 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <path
            d="m7 10 5 5 5-5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          aria-labelledby={id}
          className="absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl shadow-slate-900/10"
        >
          {options.map((option) => {
            const selected = option.value === value;

            return (
              <li key={option.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  onClick={() => {
                    onChange({
                      target: { name, value: option.value },
                    });
                    setOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                    selected
                      ? "bg-cyan-50 font-semibold text-cyan-800"
                      : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <span>{option.label}</span>

                  {selected && (
                    <svg
                      className="h-4 w-4 text-cyan-700"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      aria-hidden="true"
                    >
                      <path
                        d="m5 12 4 4L19 6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
