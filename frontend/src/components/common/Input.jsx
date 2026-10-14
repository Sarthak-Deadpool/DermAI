function Input({
    label,
    id,
    type = "text",
    name,
    value,
    onChange,
    placeholder = "",
    required = true,
    autoComplete,
    minLength,
    maxLength,
}) {
    return (
      <div>
        <label
          htmlFor={id}
          className="block text-sm font-medium text-slate-200"
        >
          {label}
        </label>
        <input
          id={id}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          autoComplete={autoComplete}
          minLength={minLength}
          maxLength={maxLength}
          className={`w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20`}
        />
      </div>
    );
}

export default Input