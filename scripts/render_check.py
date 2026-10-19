"""HWPX -> PDF -> PNG 변환 (시각 검증용).

사용법: python render_check.py 문서.hwpx [dpi]
pywin32(win32com)와 PyMuPDF(fitz) 필요:  pip install pywin32 pymupdf
성공하면 문서.hwpx 옆에 문서.pdf, 문서_p1.png ... 가 생긴다.
PDF가 만들어진다는 것 자체가 "한글이 이 hwpx를 열었다"는 증거다.
"""
import os
import sys
import time
import win32com.client
import fitz

sys.stdout.reconfigure(encoding="utf-8")


def hwpx_to_pdf(hwpx_path, pdf_path):
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    try:
        for attempt in range(3):
            try:
                hwp.Open(hwpx_path, "", "forceopen:true")
                hwp.HAction.GetDefault("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
                hwp.HParameterSet.HFileOpenSave.filename = pdf_path
                hwp.HParameterSet.HFileOpenSave.Format = "PDF"
                hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
                hwp.Clear(1)
                return True
            except Exception as e:
                print(f"[재시도 {attempt+1}/3] {e}")
                try:
                    hwp.Clear(1)
                except Exception:
                    pass
                time.sleep(2 ** attempt)
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass
    return False


def pdf_to_pngs(pdf_path, dpi=150):
    doc = fitz.open(pdf_path)
    paths = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat)
        out = pdf_path.rsplit(".", 1)[0] + f"_p{i+1}.png"
        pix.save(out)
        paths.append(out)
    doc.close()
    return paths


def main():
    if len(sys.argv) < 2:
        print("사용법: python render_check.py 문서.hwpx [dpi]")
        return
    hwpx = os.path.abspath(sys.argv[1])
    dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    pdf = hwpx.rsplit(".", 1)[0] + ".pdf"

    print(f"HWPX: {hwpx}")
    if not os.path.exists(hwpx):
        print("파일 없음")
        return
    if not hwpx_to_pdf(hwpx, pdf) or not os.path.exists(pdf):
        print("PDF 변환 실패 — 한글이 파일을 열지 못했을 가능성")
        return
    print(f"PDF: {pdf}")
    for p in pdf_to_pngs(pdf, dpi):
        print(f"PNG: {p}")


if __name__ == "__main__":
    main()
