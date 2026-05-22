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

    expect(template).toContain(
      'By clicking "Register", you agree to the <a class="font-semibold" href="#" target="__blank">Terms of Service</a>'
    );
    expect(template).toContain(
      "California residents: see our Privacy Policy for your rights under the CCPA/CPRA and the “Do Not Sell My Personal Information” option"
    );
  });
});