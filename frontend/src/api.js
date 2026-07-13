const API_BASE = "http://localhost:8000";

export async uploadProposal(file){
    const formData = new FormData();
    FormData.append("file", file);

    const res = await fetch(`${API_BASE}/api/proposals/upload`, {
        method: "POST",
        body: formData


    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed")
    }
    return res.json();


}

