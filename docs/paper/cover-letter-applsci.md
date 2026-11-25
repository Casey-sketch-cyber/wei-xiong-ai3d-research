*Date: [Month DD, YYYY — to be completed by the author]*

To the Editorial Office and Editor-in-Chief  
*Applied Sciences* (MDPI)  
Section: Computing and Artificial Intelligence

Dear Editors,

We are pleased to submit our original research article, **"Three Protocol Choices Shape Measured Fidelity of AI Inpainting on Museum Paintings,"** for consideration as an Article in *Applied Sciences* under the section **Computing and Artificial Intelligence**.

Off-the-shelf image inpainting models are increasingly evaluated for visualizing localized losses in digitized museum paintings, yet published benchmarks rarely document low-level pipeline details that can substantially alter full-reference error scores and effective sample coverage. Building on prior multi-model painting-inpainting studies and recent technical observations on latent-space mask quantization and diffusion initialization, our manuscript systematically quantifies three protocol choices—8× nearest-neighbor latent-space mask downsampling, hole prefill color under partial-strength denoising, and safety-filter denominator accounting—across four pinned models (LaMa, MAT, PowerPaint v1, and SDXL Inpainting) and 120 open-access paintings from two independent museum collections (the Cleveland Museum of Art and the Art Institute of Chicago), stratified across four physical medium-and-support groups and six procedural damage geometries. We show that while these three protocol choices can shift measured error far beyond practical margins and substantially alter sample availability, the controlled ranking (`LaMa ≈ MAT < PowerPaint v1 < SDXL`) held identically across both museums, all four painting media, and all six damage conditions.

This work aligns directly with the **Computing and Artificial Intelligence** section of *Applied Sciences*. It addresses applied computer vision and generative AI benchmarking, diagnoses concrete architectural and deployment mechanisms in widely used pixel-space and latent diffusion pipelines, and delivers actionable reporting standards and model-selection guidance for museum digitization and cultural-heritage computing workflows. All experimental protocols, code, and checksums are documented for transparent reproducibility.

We confirm that **this manuscript has not been published previously and is not under consideration for publication elsewhere.** We further confirm that **all authors have read and approved the manuscript and agree to its submission to *Applied Sciences*.** The use of generative AI tools during code development, verification, and manuscript preparation is transparently disclosed in both Section 3.5 and the Acknowledgments in accordance with MDPI guidelines.

Thank you for your time and consideration.

Sincerely,

*[Author Full Name — to be completed by the author]*  
*[Department / Institution — to be completed by the author]*  
*[City, Country — to be completed by the author]*  
*[Corresponding Email Address — to be completed by the author]*
