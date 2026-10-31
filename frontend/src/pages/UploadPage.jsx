import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Camera, Check, FileImage, ImagePlus, RefreshCw, UploadCloud, X } from "lucide-react";
import { caseApi, imageApi } from "../api/services";
import { errorMessage } from "../api/client";
import { Button, EmptyState, Loading, Notice, PageTitle } from "../components/ui";

const MAX_BYTES = 10 * 1024 * 1024;
const MAX_PIXELS = 25_000_000;
const MIN_SIDE = 100;

export default function UploadPage() {
  const [params] = useSearchParams();
  const initialCase = params.get("case");
  const [cases, setCases] = useState([]);
  const [caseId, setCaseId] = useState(initialCase || "");
  const [images, setImages] = useState([]);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [dragging, setDragging] = useState(false);
  const galleryRef = useRef(null);
  const captureRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    let active = true;
    caseApi.list({ offset: 0, limit: 100 }).then((result) => { if (active) { setCases(result); if (initialCase && result.some((item) => item.id === initialCase)) setCaseId(initialCase); else if (!initialCase && result[0]) setCaseId(result[0].id); } }).catch((err) => { if (active) setError(errorMessage(err, "Could not load your cases.")); }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [initialCase]);
  useEffect(() => {
    if (!caseId) { setImages([]); return undefined; }
    let active = true;
    imageApi.list(caseId).then((result) => { if (active) setImages(result); }).catch((err) => { if (active) setError(errorMessage(err, "Could not load case images.")); });
    return () => { active = false; };
  }, [caseId]);
  useEffect(() => { if (!file) { setPreviewUrl(""); return undefined; } const url = URL.createObjectURL(file); setPreviewUrl(url); return () => URL.revokeObjectURL(url); }, [file]);
  useEffect(() => () => streamRef.current?.getTracks().forEach((track) => track.stop()), []);
  useEffect(() => { if (cameraOpen && videoRef.current && streamRef.current) videoRef.current.srcObject = streamRef.current; }, [cameraOpen]);

  async function acceptFile(candidate) {
    setError(""); setNotice("");
    if (!candidate) return;
    if (!["image/jpeg", "image/png"].includes(candidate.type)) { setError("Choose a JPEG or PNG image."); return; }
    if (candidate.size > MAX_BYTES) { setError("This image is larger than the 10 MB upload limit."); return; }
    try {
      const bitmap = await createImageBitmap(candidate);
      const { width, height } = bitmap; bitmap.close();
      if (Math.min(width, height) < MIN_SIDE) { setError(`Image dimensions must be at least ${MIN_SIDE} pixels on each side. Selected: ${width} × ${height}.`); return; }
      if (width * height > MAX_PIXELS) { setError("This image exceeds the 25 megapixel limit."); return; }
      setFile(candidate);
    } catch { setError("The selected file could not be decoded as an image."); }
  }

  async function startCamera() {
    setCameraError("");
    if (!navigator.mediaDevices?.getUserMedia) { setCameraError("Camera capture is unavailable in this browser. Use the photo library instead."); return; }
    try { streamRef.current = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false }); setCameraOpen(true); }
    catch (err) { setCameraError(err.name === "NotAllowedError" ? "Camera permission was denied. You can still choose an image from your library." : "Could not access a camera. Check browser permissions or choose a photo instead."); }
  }
  function stopCamera() { streamRef.current?.getTracks().forEach((track) => track.stop()); streamRef.current = null; setCameraOpen(false); }
  function captureFrame() {
    const video = videoRef.current;
    if (!video?.videoWidth) { setCameraError("The camera is not ready yet."); return; }
    const canvas = document.createElement("canvas"); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob((blob) => { if (blob) { const captured = new File([blob], `dermai-capture-${Date.now()}.jpg`, { type: "image/jpeg" }); acceptFile(captured); stopCamera(); } }, "image/jpeg", 0.92);
  }
  async function upload() {
    if (!caseId || !file) return;
    setUploading(true); setProgress(0); setError(""); setNotice("");
    try { const result = await imageApi.upload(caseId, file, (event) => event.total && setProgress(Math.round((event.loaded / event.total) * 100))); setImages((current) => [result, ...current]); setFile(null); setNotice("Image uploaded and stored successfully."); }
    catch (err) { setError(errorMessage(err, "The image could not be uploaded.")); }
    finally { setUploading(false); }
  }

  return <div className="mx-auto max-w-5xl space-y-7"><PageTitle eyebrow="Image intake" title="Add a skin image" description="Choose an existing case, then use the camera or select a JPEG or PNG photo. The backend validates and securely processes each upload."/>
    {error && <Notice kind="error">{error}</Notice>}{notice && <Notice kind="success">{notice}</Notice>}
    {loading ? <Loading label="Loading cases"/> : cases.length === 0 ? <section className="rounded-2xl border border-[#e4e1da] bg-white"><EmptyState icon={FileImage} title="Start with a case" description="An image must belong to a case. Create a case record first, then return here to add an image." action={<Button as={Link} to="/app/cases/new">Create a case</Button>}/></section> : <>
      <label className="block max-w-lg text-sm font-semibold text-[#484640]">Case for this image<select value={caseId} onChange={(event) => { setCaseId(event.target.value); setFile(null); setNotice(""); }} className="mt-2 w-full rounded-lg border border-[#d9d6ce] bg-white px-3 py-2.5 font-normal"><option value="">Select a case</option>{cases.map((item) => <option key={item.id} value={item.id}>{item.case_label || "Untitled case"} · {item.body_location || "Location not recorded"}</option>)}</select></label>
      {caseId && <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(300px,0.75fr)]">
        <section className="space-y-4 rounded-2xl border border-[#e4e1da] bg-white p-5 sm:p-7"><div><h2 className="font-semibold">Choose an image</h2><p className="mt-1 text-sm text-[#77746c]">Capture a new photo or select an existing JPEG or PNG image.</p></div>
          {cameraError && <Notice kind="warning">{cameraError}</Notice>}
          {cameraOpen ? <div className="space-y-3"><video ref={videoRef} autoPlay muted playsInline className="max-h-[55vh] w-full rounded-xl bg-[#292823] object-contain"/><div className="flex flex-wrap gap-2"><Button onClick={captureFrame}><Camera size={16}/>Capture photo</Button><Button variant="secondary" onClick={stopCamera}><X size={16}/>Cancel camera</Button></div></div> : <><div onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files?.[0]); }} className={`rounded-xl border border-dashed p-6 text-center transition sm:p-10 ${dragging ? "border-[#bd6545] bg-[#fbf3ed]" : "border-[#d9d6ce] bg-[#fcfbf9]"}`}><span className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[#f1e9e1] text-[#97563c]"><UploadCloud size={22}/></span><p className="mt-4 text-sm font-semibold">Drop an image here</p><p className="mt-1 text-xs text-[#858178]">JPEG or PNG · 10 MB maximum</p><div className="mt-5 flex flex-wrap justify-center gap-2"><Button variant="secondary" onClick={() => galleryRef.current?.click()}><FileImage size={16}/>Choose from gallery</Button><Button variant="secondary" onClick={startCamera}><Camera size={16}/>Live camera</Button><Button variant="quiet" onClick={() => captureRef.current?.click()}>Open device camera</Button></div><input ref={galleryRef} type="file" accept="image/jpeg,image/png" className="sr-only" onChange={(event) => { acceptFile(event.target.files?.[0]); event.target.value = ""; }}/><input ref={captureRef} type="file" accept="image/jpeg,image/png" capture="environment" className="sr-only" onChange={(event) => { acceptFile(event.target.files?.[0]); event.target.value = ""; }}/></div>
          </>}
          {file && <div className="overflow-hidden rounded-xl border border-[#e4e1da]"><div className="flex items-center justify-between border-b border-[#eeece6] px-4 py-3"><div className="min-w-0"><p className="truncate text-sm font-semibold">{file.name}</p><p className="mt-0.5 text-xs text-[#817d73]">{(file.size / 1024 / 1024).toFixed(2)} MB · {file.type}</p></div><button type="button" onClick={() => setFile(null)} aria-label="Remove selected image" className="rounded-md p-2 text-[#77746c] hover:bg-[#f2efe8]"><X size={17}/></button></div><img src={previewUrl} alt="Selected skin image preview" className="max-h-[420px] w-full bg-[#f4f2ed] object-contain"/><div className="flex items-center justify-between gap-3 border-t border-[#eeece6] px-4 py-3"><p className="text-xs leading-5 text-[#77746c]">Preview only. The server validates the image before storage.</p><Button disabled={uploading} onClick={upload}>{uploading ? `Uploading ${progress}%` : <><ImagePlus size={16}/>Upload image</>}</Button></div>{uploading && <div className="h-1 bg-[#eeeae2]"><div className="h-full bg-[#bd6545] transition-all" style={{ width: `${progress}%` }}/></div>}</div>}
        </section>
        <aside className="space-y-4"><section className="rounded-2xl border border-[#e4e1da] bg-white p-5"><h2 className="font-semibold">Before you upload</h2><ul className="mt-3 space-y-2.5 text-sm leading-5 text-[#6f6c64]"><li className="flex gap-2"><Check size={15} className="mt-0.5 shrink-0 text-[#7a8b61]"/>Use a well-lit, focused image.</li><li className="flex gap-2"><Check size={15} className="mt-0.5 shrink-0 text-[#7a8b61]"/>Keep the area of interest in frame.</li><li className="flex gap-2"><Check size={15} className="mt-0.5 shrink-0 text-[#7a8b61]"/>The API accepts JPEG and PNG images.</li><li className="flex gap-2"><Check size={15} className="mt-0.5 shrink-0 text-[#7a8b61]"/>Each side must be at least 100 px; maximum 25 megapixels.</li></ul><p className="mt-4 border-t border-[#eeece6] pt-4 text-xs leading-5 text-[#8b887f]">Image quality scoring and recapture recommendations are not available from the backend.</p></section>
          <section className="rounded-2xl border border-[#e4e1da] bg-white p-5"><div className="flex items-center justify-between"><div><h2 className="font-semibold">Images in this case</h2><p className="mt-1 text-xs text-[#89867e]">{images.length} uploaded</p></div><RefreshCw size={16} className="text-[#99958c]"/></div>{images.length === 0 ? <p className="mt-4 text-sm text-[#77746c]">No images have been added yet.</p> : <ul className="mt-3 divide-y divide-[#efede8]">{images.slice(0, 6).map((image) => <li key={image.id} className="flex items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="truncate text-xs font-semibold">{image.original_filename || image.id}</p><p className="mt-1 text-[11px] text-[#89867e]">{image.width} × {image.height} · {(image.file_size / 1024).toFixed(0)} KB</p></div><Link to={`/app/cases/${caseId}/images/${image.id}`} className="shrink-0 text-xs font-semibold text-[#a25539] hover:underline">Review</Link></li>)}</ul>}</section>
          <Notice kind="info">Uploading stores the image under its case. No diagnosis, risk score, or quality result is generated.</Notice>
        </aside>
      </div>}
    </>}
  </div>;
}
