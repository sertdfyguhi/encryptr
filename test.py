from encryptr import EncryptrFile

file = EncryptrFile("test.enc", "password")
file.root["test.txt"] = b"test"
file.root["dir"] = {"test2.txt": b"test2"}
file.root["dir"]["dir2"] = {}
file.save()
