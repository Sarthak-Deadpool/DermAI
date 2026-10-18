/** @format */

import { useEffect, useRef, useState } from "react";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function ImageUpload({ onFileChange, disabled = false }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const inputRef = useRef(null);

  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  function handleFile(selectedFile) {
    setError("");

    if (!selectedFile) return;

    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      setError("Please select a JPG or PNG");
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("Image size must be 10 MB or less.");
      return;
    }

    setFile(selectedFile);
    onFileChange?.(selectedFile);
  }

  function handleInputChange(event) {
    const selectedFile = event.target.files?.[0];

    if (selectedFile) {
      handleFile(selectedFile);
    }

    // Allows selecting the same file again.
    event.target.value = "";
  }

  function removeFile() {
    setFile(null);
    setPreview("");
    setError("");
    onFileChange?.(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const droppedFile = event.dataTransfer.files?.[0];

    if (droppedFile) {
      handleFile(droppedFile);
    }
  }

  return (
    <div className="w-full space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-slate-800">Skin Image</h3>
        <p className="mt-1 text-sm text-slate-500">
          Upload a clear image for your research case.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleInputChange}
        disabled={disabled}
        className="hidden"
      />

      {!file ? (
        <div
          onDragOver={(event) => {
            event.preventDefault();
            if (!disabled) setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`rounded-2xl border-2 border-dashed p-6 text-center transition sm:p-10 ${
            isDragging
              ? "border-cyan-500 bg-cyan-50"
              : "border-slate-300 bg-slate-50 hover:border-cyan-400 hover:bg-cyan-50/40"
          } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
        >
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              className="h-7 w-7"
              aria-hidden="true"
            >
              <path
                d="M12 16V4m0 0L7 9m5-5 5 5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M4 16.5v2A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5v-2"
                strokeLinecap="round"
              />
            </svg>
          </div>

          <p className="mt-4 text-sm font-semibold text-slate-800">
            Drag and drop your image here
          </p>

          <p className="mt-1 text-sm text-slate-500">
            or browse files from your device
          </p>

          <button
            type="button"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
            className="mt-5 inline-flex items-center justify-center rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700 focus:outline-none focus:ring-4 focus:ring-cyan-600/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Browse Images
          </button>

          <p className="mt-4 text-xs text-slate-400">
            JPG, PNG or WebP · Maximum 10 MB
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-800">
                Selected Image
              </p>
              <p className="mt-0.5 truncate text-xs text-slate-500">
                {file.name}
              </p>
            </div>

            <span className="ml-3 shrink-0 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
              Selected
            </span>
          </div>

          <div className="flex min-h-56 items-center justify-center bg-slate-50 p-4">
            <img
              src={preview}
              alt="Selected skin image preview"
              className="max-h-80 max-w-full rounded-lg object-contain"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <p className="text-sm font-medium text-slate-700">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <p className="text-xs text-slate-500">Preview ready</p>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={disabled}
                onClick={() => inputRef.current?.click()}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
              >
                Change
              </button>

              <button
                type="button"
                disabled={disabled}
                onClick={removeFile}
                className="rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-60"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </p>
      )}
    </div>
  );
}
