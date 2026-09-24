# Readur vs Paperless

This page helps you decide between Readur and Paperless for your document
management needs. It covers the design differences, the workflows each tool
favors, and how to move your documents over from Paperless if you decide to
switch.

## Why the comparison exists

People coming from Paperless often ask what makes Readur different and which
tool fits their setup. Both projects solve the same core problem. They turn a
pile of scanned and digital documents into a searchable, organized archive.
The two tools make different tradeoffs in how they get there.

## Design philosophy

Paperless is a mature Python project built on Django. It has been around for
years and carries a large set of plugins, integrations, and community
tutorials. Its strength is depth. You get a rich set of classification tools,
email consumption, and a broad REST API that many third-party tools already
speak.

Readur is a newer project with a Rust backend and a React frontend. It focuses
on a fast, modern interface and a smaller, more opinionated feature set. The
Rust backend gives it a lightweight footprint and quick startup, which suits
self-hosters who want a snappy tool on modest hardware.

## Feature comparison

Both tools handle the essentials well. They accept PDFs, images, and office
documents, run OCR to extract text, and index that text for full-text search.

| Area | Readur | Paperless |
|------|--------|-----------|
| Backend | Rust | Python (Django) |
| Frontend | React with Material UI | Angular |
| OCR | Tesseract, multi-language | Tesseract, multi-language |
| Search | PostgreSQL full-text with simple, phrase, fuzzy, and boolean modes | PostgreSQL or Redis full-text |
| Organization | Labels with color coding and hierarchy | Tags, correspondents, document types, custom fields |
| Authentication | JWT with bcrypt, OIDC and SSO support | Built-in users, optional OIDC and LDAP |
| Sync sources | WebDAV, local folders, S3 | Watch folders, email (IMAP), scanner, S3 via plugins |
| API | Swagger UI built in | REST API with broad third-party support |
| Deployment | Docker, self-hosted | Docker, bare metal, self-hosted |

## Workflow differences

Paperless leans on automation. You point it at a watch folder or an email
inbox and it consumes, classifies, and files documents on its own. Its
classification rules let you assign tags, correspondents, and document types
automatically based on content. This suits people who want a hands-off
pipeline.

Readur favors a more direct workflow. You'll upload or sync documents and
organize them with labels. Its folder monitoring watches directories without
moving or altering your files, which is useful if you want to keep your
original folder structure intact. The search modes give you fine control over
how you query your archive.

## Which tool should you choose

Choose Paperless if you want the most mature tool, automatic email and
watch-folder consumption, and the widest range of plugins and integrations.
It is the safer bet for large archives and complex classification rules.

Choose Readur if you want a modern, fast interface, a lightweight Rust backend,
and a simpler, more opinionated tool. It is a good fit if you prefer labels
over a complex classification model and want to keep your source folders
untouched.

## Migrating from Paperless

Moving your documents from Paperless to Readur is mostly a matter of exporting
your files and re-importing them. The two tools store documents differently,
so you'll re-apply your organization in Readur.

### Export your documents from Paperless

Paperless has a built-in exporter. From the admin interface, run the document
exporter to produce a zip archive of your documents and their metadata. You
can also export just the files if you only want the originals.

### Import into Readur

Upload the exported files through the Readur web interface or place them in a
watched folder. Readur will run OCR and index the text automatically. If you
used the folder monitoring feature, drop the files into a directory Readur is
watching and let it pick them up.

### Rebuild your organization

Paperless tags, correspondents, and document types do not map one to one onto
Readur labels. Plan a label scheme before you import. Readur labels support
color coding and hierarchy, so you can recreate a similar structure with a
top-level label for each correspondent and child labels for document types.

### What does not carry over

Paperless custom fields and saved views have no direct equivalent in Readur.
You'll recreate those as labels or search bookmarks. Email consumption rules
also do not transfer, so set up your sync sources in Readur after the move.

## Getting help

If you run into trouble during the move, the Readur troubleshooting guide and
the migration guide cover common issues. The community is active on the
project repository and happy to help with specific migration questions.
