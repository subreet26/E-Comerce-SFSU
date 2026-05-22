import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

describe("registration disclosure", () => {
  it("includes the required terms and privacy policy notice", () => {
    const specDir = path.dirname(fileURLToPath(import.meta.url));
    const templatePath = path.resolve(
      specDir,
      "../marketplace/templates/marketplace/register.html",
    );

    const template = fs.readFileSync(templatePath, "utf8");
    const visibleText = template.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();

    expect(visibleText).toContain(
      'By clicking "Register", you agree to the Terms of Service and Privacy Policy. California residents: see our Privacy Policy for your rights under the CCPA/CPRA and the “Do Not Sell My Personal Information” option.'
    );
  });
});